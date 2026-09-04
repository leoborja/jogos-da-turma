#!/usr/bin/env python3
"""
gerador.py — monta o banco de cartas "Top 10" (países / línguas)
a partir de fontes abertas: Banco Mundial (WDI) + Wikidata.

Uso:
    python gerador.py                 # gera o banco
    python gerador.py --listar        # baixa a lista de indicadores do WDI
    python gerador.py --manter-disputadas
    python gerador.py --min-paises 40
    python gerador.py --incluir-territorios   # deixa Hong Kong, Porto Rico etc.

Saídas:
    banco.json      -> o banco pronto pro site
    revisao.csv     -> uma linha por carta, pra conferir com o olho
    relatorio.txt   -> o que falhou e por quê
    cache/          -> respostas cruas das APIs (re-rodar fica instantâneo)

Nota: o REST Countries foi descontinuado (v3.1/v4/v5 devolvem "deprecated").
Nome em português e apelidos vêm do Wikidata via SPARQL.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict

import requests

from indicadores import (INDICADORES, REGIOES, NAO_SOBERANOS, NOMES_EXTRA,
                         APELIDOS_EXTRA, UE27, VETADAS, FATIA_0_100,
                         regiao_de)
from linguas import cartas_de_linguas
from brasil import cartas_do_brasil
from notas import NOTAS

WB = "https://api.worldbank.org/v2"
SPARQL = "https://query.wikidata.org/sparql"
UA = "JogosDaTurma/0.1 (https://github.com/leoborja; leo@cloudarbitration.com)"
CACHE = "cache"
ANO_INI, ANO_FIM = 2010, 2026


# ---------------------------------------------------------------- utilidades

def norm(s):
    """minúscula, sem acento, sem pontuação — pra comparar palpite com resposta."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def fmt_valor(v, fmt):
    """Formata o número do jeito que o juiz lê em voz alta e encerra a discussão."""
    def br(x, casas=0):
        s = f"{x:,.{casas}f}"
        return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

    if fmt == "usd":
        a = abs(v)
        if a >= 1e12:
            return f"US$ {br(v/1e12, 2)} tri"
        if a >= 1e9:
            return f"US$ {br(v/1e9, 1)} bi"
        if a >= 1e6:
            return f"US$ {br(v/1e6, 1)} mi"
        return f"US$ {br(v, 0)}"
    if fmt == "pct":
        return f"{br(v, 1)}%"
    if fmt == "dec":
        return br(v, 1 if abs(v) >= 10 else 2)
    if fmt == "anos":
        return f"{br(v, 1)} anos"
    if fmt == "km2":
        return f"{br(v, 0)} km²"
    a = abs(v)
    if a >= 1e9:
        return f"{br(v/1e9, 2)} bi"
    if a >= 1e6:
        return f"{br(v/1e6, 1)} mi"
    return br(v, 0)


def get(url, params=None, chave=None, headers=None):
    """GET com cache em disco. chave = nome do arquivo no cache/."""
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, f"{chave}.json") if chave else None
    if caminho and os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    r = requests.get(url, params=params, timeout=120,
                     headers={"User-Agent": UA, **(headers or {})})
    r.raise_for_status()
    dados = r.json()
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f)
    time.sleep(0.3)
    return dados


def get_texto(url, chave):
    """GET com cache em disco pra arquivo de texto (o CSV do Glottolog)."""
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, f"{chave}.csv")
    if os.path.exists(caminho):
        return open(caminho, encoding="utf-8").read()
    r = requests.get(url, timeout=180, headers={"User-Agent": UA})
    r.raise_for_status()
    open(caminho, "w", encoding="utf-8").write(r.text)
    time.sleep(0.3)
    return r.text


def get_json(url, chave):
    """GET de JSON por URL inteira (as APIs do IBGE já vêm com querystring)."""
    return get(url, None, chave)


def sparql(query, chave):
    return get(SPARQL, {"query": query, "format": "json"}, chave,
               {"Accept": "application/sparql-results+json"})


# ---------------------------------------------------------------- fontes

def carrega_paises(incluir_territorios=False):
    """iso3 -> {nome_en, regiao}. Só países de verdade: fora os agregados."""
    d = get(f"{WB}/country", {"format": "json", "per_page": 400}, "wb_paises")
    saida = {}
    for c in d[1]:
        if c["region"]["value"] == "Aggregates":
            continue
        if not incluir_territorios and c["id"] in NAO_SOBERANOS:
            continue
        saida[c["id"]] = {"nome_en": c["name"], "iso2": c["iso2Code"],
                          "regiao": regiao_de(c["id"], c["region"]["value"].strip())}
    return saida


Q_NOMES = """
SELECT ?iso3 ?ptbr ?pt ?apelido WHERE {
  ?p wdt:P298 ?iso3 .
  OPTIONAL { ?p rdfs:label    ?ptbr    . FILTER(LANG(?ptbr) = "pt-br") }
  OPTIONAL { ?p rdfs:label    ?pt      . FILTER(LANG(?pt)   = "pt") }
  OPTIONAL { ?p skos:altLabel ?apelido . FILTER(LANG(?apelido) IN ("pt", "pt-br")) }
}
"""


def carrega_nomes_pt(paises, problemas):
    """iso3 -> {'nome': 'Brasil', 'apelidos': [...normalizados...]} via Wikidata."""
    d = sparql(Q_NOMES, "wd_nomes_pt")
    rotulos, brutos = {}, defaultdict(set)
    for b in d["results"]["bindings"]:
        iso = b["iso3"]["value"]
        if iso not in paises:
            continue
        for chave in ("ptbr", "pt"):
            if chave in b:
                brutos[iso].add(b[chave]["value"])
                rotulos.setdefault(iso, b[chave]["value"])   # pt-br ganha do pt
        if "apelido" in b:
            brutos[iso].add(b["apelido"]["value"])
    rotulos.update({k: v for k, v in NOMES_EXTRA.items() if k in paises})

    # APELIDOS_EXTRA manda: é a lista curada pra mesa. Se um apelido do
    # Wikidata bate com um apelido curado de OUTRO país, o do Wikidata cai.
    reservado = {}
    for iso, lista in APELIDOS_EXTRA.items():
        for a in lista:
            n = norm(a)
            if n in reservado and reservado[n] != iso:
                problemas.append(
                    f"APELIDOS_EXTRA: '{n}' está em {reservado[n]} e {iso}")
            reservado[n] = iso

    cand = {}
    for iso in paises:
        s = set()
        for b in brutos.get(iso, ()):
            n = norm(b)
            if len(n) > 2 and reservado.get(n, iso) == iso:
                s.add(n)
        s.add(norm(paises[iso]["nome_en"]))
        s |= {norm(a) for a in APELIDOS_EXTRA.get(iso, ())}
        cand[iso] = {n for n in s if len(n) > 2}

    # apelido que aponta pra dois países é pior que apelido nenhum: some
    dono = defaultdict(set)
    for iso, s in cand.items():
        for n in s:
            dono[n].add(iso)
    ambiguos = {n for n, isos in dono.items() if len(isos) > 1}
    for n in sorted(ambiguos):
        if n not in reservado:
            problemas.append(f"apelido ambíguo descartado: '{n}' -> "
                             + ", ".join(sorted(dono[n])))

    saida = {}
    for iso, p in paises.items():
        nome = NOMES_EXTRA.get(iso) or rotulos.get(iso) or p["nome_en"]
        aps = sorted((cand[iso] - ambiguos) | {norm(nome)})
        saida[iso] = {"nome": nome, "apelidos": aps}
        if iso not in rotulos and iso not in NOMES_EXTRA:
            problemas.append(f"sem nome em português no Wikidata: {iso} "
                             f"({p['nome_en']}) — usando o nome em inglês")
    return saida


def definicao(codigo):
    """
    Definição oficial do indicador, palavra por palavra como o Banco Mundial
    publica. É o que sustenta a nota em português quando alguém na mesa duvida.
    """
    d = get(f"{WB}/indicator/{codigo}", {"format": "json"}, f"def_{codigo}")
    try:
        return d[1][0]
    except (TypeError, IndexError, KeyError):
        return None


def serie(codigo):
    """Todas as observações do indicador no período. [] se o código não existe."""
    d = get(f"{WB}/country/all/indicator/{codigo}",
            {"format": "json", "per_page": 20000, "date": f"{ANO_INI}:{ANO_FIM}"},
            f"wb_{codigo}")
    if not isinstance(d, list) or len(d) < 2 or d[1] is None:
        return []
    return d[1]


def populacoes(paises):
    """iso3 -> população mais recente, pro filtro min_pop."""
    pop = {}
    for r in serie("SP.POP.TOTL"):
        iso, v = r.get("countryiso3code"), r.get("value")
        if iso in paises and v:
            ano = int(r["date"])
            if iso not in pop or ano > pop[iso][0]:
                pop[iso] = (ano, v)
    return {k: v[1] for k, v in pop.items()}


# ---------------------------------------------------------------- montagem

def melhor_ano(linhas, paises):
    """
    Ranking só vale comparando o MESMO ano. Escolhe o ano mais recente
    que ainda tem cobertura decente (>= 80% do melhor ano do período).
    """
    por_ano = defaultdict(int)
    for r in linhas:
        if r.get("countryiso3code") in paises and r.get("value") is not None:
            por_ano[int(r["date"])] += 1
    if not por_ano:
        return None
    teto = max(por_ano.values())
    return max(a for a, n in por_ano.items() if n >= 0.8 * teto)


def texto_regional(pergunta, sufixo):
    return pergunta.rstrip("?").replace(" do mundo", "") + f" {sufixo}?"


def monta_carta(linhas, ano, paises, nomes, pop, ind, pergunta, maior,
                regiao=None, min_paises=30, tol=0.005):
    """Devolve uma carta ou None se não passar nos filtros de qualidade."""
    cand = []
    for r in linhas:
        iso, v = r.get("countryiso3code"), r.get("value")
        if v is None or iso not in paises or int(r["date"]) != ano:
            continue
        if regiao == "União Europeia":
            if iso not in UE27:
                continue
        elif regiao and paises[iso]["regiao"] != regiao:
            continue
        if ind["min_pop"] and pop.get(iso, 0) < ind["min_pop"]:
            continue
        cand.append((iso, float(v)))

    if len(cand) < min_paises:
        return None

    cand.sort(key=lambda x: x[1], reverse=maior)
    dez, onze = cand[:10], cand[10]

    # fatia de um todo que passa de 100% não é a fatia que o enunciado promete
    if ind["cod"] in FATIA_0_100:
        fora = [v for _, v in dez if v < 0 or v > 100]
        if fora:
            return {"_furada": f"{ind['cod']}: valor fora de 0-100% ({max(fora):.1f}) "
                               f"— a métrica não é a fatia que a pergunta promete"}

    # 10º e 11º empatados na prática = carta injusta: o jogador acerta e "erra"
    a, b = abs(dez[-1][1]), abs(onze[1])
    disputada = abs(a - b) <= tol * max(a, b, 1e-9)

    return {
        "tema": "paises",
        "tipo_resposta": "pais",
        "pergunta": texto_regional(pergunta, REGIOES[regiao]) if regiao else pergunta,
        "escopo": regiao or "mundo",
        "fonte": "Banco Mundial",
        "indicador": ind["cod"],
        "ano": ano,
        "unidade": ind["unidade"],
        "universo": len(cand),
        "disputada": disputada,
        "folga": round(abs(a - b) / max(a, b, 1e-9), 4),
        "respostas": [
            {"pos": i + 1, "chave": iso, "nome": nomes[iso]["nome"],
             "valor": val, "valor_fmt": fmt_valor(val, ind["fmt"])}
            for i, (iso, val) in enumerate(dez)
        ],
    }


def deduplica(cartas, teto, problemas, global_tambem=True):
    """
    Dentro de um mesmo escopo, "quem mais exporta", "maior PIB" e "quem mais
    emite CO2" devolvem quase a mesma lista. Pergunta diferente com a mesma
    resposta é carta repetida: na mesa o jogador decora o top 10 e ganha
    a rodada seguinte de graça.

    Percorre as cartas na ordem do catálogo e só mantém a que não repete
    mais de `teto` do top 10 de alguma carta já mantida no mesmo escopo.
    """
    mantidas, vistas, todas = [], defaultdict(list), []
    for c in cartas:
        atual = {r.get("chave") or r["nome"] for r in c["respostas"]}
        choque = None
        for anterior, conj in vistas[c["escopo"]]:
            if len(atual & conj) / len(atual | conj) > teto:
                choque = anterior
                break
        # Recorte diferente do MESMO indicador é carta legítima (a Ásia é um
        # pedaço do mundo). Mas "nomes mais comuns em SP" e "em MG" devolvem
        # a mesma lista com outra bandeira — isso é repetição, não recorte.
        # Daí a segunda passada, que compara tudo com tudo, com régua maior.
        if not choque and global_tambem:
            for anterior, conj in todas:
                if len(atual & conj) / len(atual | conj) > 0.7:
                    choque = anterior
                    break
        if choque:
            problemas.append(f"repetida: '{c['pergunta']}' devolve quase o mesmo "
                             f"top 10 de '{choque}'")
        else:
            mantidas.append(c)
            vistas[c["escopo"]].append((c["pergunta"], atual))
            todas.append((c["pergunta"], atual))
    return mantidas


# ---------------------------------------------------------------- extras

def listar_indicadores():
    """Baixa o catálogo do WDI pra garimpar mais perguntas."""
    linhas, pagina = [], 1
    while True:
        d = get(f"{WB}/indicator", {"format": "json", "source": 2,
                                    "per_page": 500, "page": pagina},
                f"wb_catalogo_{pagina}")
        linhas += d[1]
        if pagina >= int(d[0]["pages"]):
            break
        pagina += 1
    with open("indicadores_wdi.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "nome"])
        for i in linhas:
            w.writerow([i["id"], i["name"]])
    print(f"indicadores_wdi.csv — {len(linhas)} indicadores disponíveis")


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--manter-disputadas", action="store_true")
    ap.add_argument("--incluir-territorios", action="store_true")
    ap.add_argument("--min-paises", type=int, default=60)
    ap.add_argument("--min-paises-regiao", type=int, default=22)
    ap.add_argument("--max-sobreposicao", type=float, default=0.6,
                    help="quanto do top 10 uma carta pode repetir de outra")
    ap.add_argument("--tolerancia", type=float, default=0.005,
                    help="folga mínima entre 10º e 11º (0.005 = 0,5%%)")
    args = ap.parse_args()

    if args.listar:
        listar_indicadores()
        return

    problemas = []
    print("baixando países...")
    paises = carrega_paises(args.incluir_territorios)
    nomes = carrega_nomes_pt(paises, problemas)
    pop = populacoes(paises)
    print(f"  {len(paises)} países (agregados e territórios descartados)")

    cartas, fichas = [], {}
    for ind in INDICADORES:
        if ind.get("_quebrado"):
            problemas.append(f"{ind['cod']} ({ind['curto']}): marcado como quebrado, pulado")
            continue
        try:
            linhas = serie(ind["cod"])
        except Exception as e:
            problemas.append(f"{ind['cod']}: erro na API ({e})")
            print(f"  {ind['cod']} FALHOU: {e}")
            continue
        if not linhas:
            problemas.append(f"{ind['cod']} ({ind['curto']}): sem dados — "
                             "código descontinuado? troque com --listar")
            print(f"  {ind['cod']} SEM DADOS")
            continue
        ano = melhor_ano(linhas, paises)
        if not ano:
            problemas.append(f"{ind['cod']}: nenhum ano com cobertura")
            continue

        if ind["cod"] not in NOTAS:
            problemas.append(f"{ind['cod']}: SEM NOTA em notas.py — carta sai "
                             "sem explicação pro juiz")
        try:
            oficial = definicao(ind["cod"]) or {}
        except Exception as e:
            oficial = {}
            problemas.append(f"{ind['cod']}: não baixou a definição oficial ({e})")
        fichas[ind["cod"]] = {
            "nome": oficial.get("name", ind["curto"]),
            "nota": NOTAS.get(ind["cod"], ""),
            "definicao": " ".join((oficial.get("sourceNote") or "").split()),
            "fonte_org": " ".join((oficial.get("sourceOrganization") or "").split())[:300],
            "url": f"https://data.worldbank.org/indicator/{ind['cod']}",
        }

        n0 = len(cartas)
        for maior, pergunta in ((True, ind["max"]), (False, ind["min"])):
            if not pergunta:
                continue
            c = monta_carta(linhas, ano, paises, nomes, pop, ind, pergunta,
                            maior, None, args.min_paises, args.tolerancia)
            if c and c.get("_furada"):
                problemas.append(c["_furada"]); c = None
            if c:
                cartas.append(c)
            else:
                problemas.append(f"{ind['cod']} global ({'maiores' if maior else 'menores'}): "
                                 f"menos de {args.min_paises} países com dado em {ano}")

        # cada indicador rende também um recorte por região
        if ind["regioes"] and ind["max"]:
            for regiao in REGIOES:
                c = monta_carta(linhas, ano, paises, nomes, pop, ind, ind["max"],
                                True, regiao, args.min_paises_regiao, args.tolerancia)
                if c and c.get("_furada"):
                    problemas.append(c["_furada"]); c = None
                if c:
                    cartas.append(c)

        print(f"  {ind['cod']:<24} {ano}  +{len(cartas)-n0} cartas")

    itens = {"pais": {iso: nomes[iso] for iso in sorted(nomes)}}

    iso2_para_iso3 = {p["iso2"]: iso for iso, p in paises.items()}
    n0 = len(cartas)
    novas = cartas_de_linguas(paises, nomes, iso2_para_iso3, get_texto,
                              sparql, norm, problemas, args.min_paises_regiao)
    cartas += novas
    print(f"  {'línguas':<24} --    +{len(cartas)-n0} cartas")
    for c in novas:
        for r in c["respostas"]:
            tipo = c["tipo_resposta"]
            itens.setdefault(tipo, {})
            if tipo != "pais":
                itens[tipo].setdefault(r["chave"],
                                       {"nome": r["nome"],
                                        "apelidos": r.pop("apelidos", [])})
            r.pop("apelidos", None)

    n0 = len(cartas)
    br, ind_mun, ind_nome = cartas_do_brasil(get_json, norm, problemas)
    cartas += br
    itens["municipio"] = ind_mun
    itens["nome"] = ind_nome
    print(f"  {'brasil':<24} --    +{len(cartas)-n0} cartas")

    # regra do jogo: carta sem explicação vira discussão na mesa
    for c in cartas:
        if not (c.get("nota") or fichas.get(c.get("indicador"), {}).get("nota")):
            problemas.append(f"SEM NOTA: '{c['pergunta']}' — o juiz não tem o que ler")

    disputadas = [c for c in cartas if c["disputada"]]
    if not args.manter_disputadas:
        cartas = [c for c in cartas if not c["disputada"]]

    vetadas = [c for c in cartas if c["pergunta"] in VETADAS]
    for c in vetadas:
        problemas.append(f"vetada à mão (fraca de jogar): '{c['pergunta']}'")
    cartas = [c for c in cartas if c["pergunta"] not in VETADAS]

    antes = len(cartas)
    cartas = deduplica(cartas, args.max_sobreposicao, problemas)
    repetidas = antes - len(cartas)

    for i, c in enumerate(cartas):
        c["id"] = f"c{i+1:04d}"

    usados = {c.get("indicador") for c in cartas}
    banco = {
        "gerado_em": time.strftime("%Y-%m-%d"),
        "indicadores": {k: v for k, v in fichas.items() if k in usados},
        "itens": itens,
        "cartas": cartas,
    }
    with open("banco.json", "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, separators=(",", ":"))

    with open("revisao.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tema", "escopo", "pergunta", "indicador", "ano",
                    "universo", "folga_10_11", "nota", "top10"])
        for c in cartas:
            w.writerow([c["id"], c["tema"], c["escopo"], c["pergunta"],
                        c.get("indicador", ""), c["ano"], c["universo"],
                        c["folga"],
                        c.get("nota") or fichas.get(c.get("indicador"), {}).get("nota", ""),
                        " | ".join(f"{r['pos']}. {r['nome']} ({r['valor_fmt']})"
                                   for r in c["respostas"])])

    with open("relatorio.txt", "w", encoding="utf-8") as f:
        f.write(f"cartas geradas: {len(cartas)}\n")
        f.write(f"descartadas por repetir o top 10 de outra: {repetidas}\n")
        f.write(f"descartadas por empate no 10º/11º: {len(disputadas)}\n")
        for c in disputadas:
            f.write(f"  - {c['pergunta']} ({c['ano']}, folga {c['folga']:.2%})\n")
        f.write(f"\nproblemas ({len(problemas)}):\n")
        f.write("\n".join(f"  - {p}" for p in problemas))

    print(f"\n{len(cartas)} cartas -> banco.json")
    print(f"{len(disputadas)} descartadas por empate no 10º/11º")
    print(f"{repetidas} descartadas por repetir o top 10 de outra carta")
    print(f"{len(problemas)} avisos -> relatorio.txt")
    print("confira revisao.csv antes de usar")


if __name__ == "__main__":
    main()
