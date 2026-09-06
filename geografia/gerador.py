#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o banco de cartas do jogo de bandeiras.

    python3 gerador.py

De onde vem cada coisa:

    Wikidata (SPARQL)   quem tem código ISO, nome em português, apelidos,
                        capital, continente, população, proporção da bandeira,
                        data de adoção e o arquivo da bandeira no Commons
    Wikimedia Commons   a imagem (PNG renderizado a partir do SVG oficial)
    Wikipédia (pt)      o parágrafo que explica a bandeira, com link
    Pageviews API       quanto o artigo do país foi lido em português nos
                        últimos 12 meses — é a régua de "mais fácil"

Nada aqui é escrito à mão além do que está em CORRECOES, APELIDOS, EXCECOES,
VETADOS e GEMEAS. Cada um desses tem comentário dizendo por que existe: são
buracos e armadilhas da fonte, não opinião nossa sobre o mundo.

O universo é a ISO 3166-1 alpha-2 — a lista de códigos de duas letras que o
mundo usa pra dizer "este é um lugar". Tem os 195 países (193 da ONU mais
Vaticano e Palestina, que são observadores) e mais uns 50 territórios.
Lista fechada e conferível: não somos nós decidindo o que é país.
"""

import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import date

import requests

SPARQL = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/"
WIKI_PT = "https://pt.wikipedia.org/api/rest_v1/page/summary/"
PAGEVIEWS = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
             "pt.wikipedia/all-access/user/{titulo}/monthly/{ini}/{fim}")
UA = "JogosDaTurma/0.1 (https://github.com/leoborja; leo@cloudarbitration.com)"
CACHE = "cache"
IMG = "img"
LARGURA = 512          # px de largura do PNG; o celular mostra a ~300 CSS px

# Rótulo do Wikidata com erro de digitação, corrigido pela grafia do
# Vocabulário Ortográfico da Língua Portuguesa.
CORRECOES = {
    "GL": "Groenlândia",   # o Wikidata traz "Groelândia", com erro de digitação
    # Nome de tratado internacional não é o nome que a mesa fala. O rótulo do
    # Wikidata é o nome longo do Estado; a carta usa o curto, que é o que
    # alguém digita olhando pra bandeira.
    "NL": "Países Baixos",        # "Reino dos Países Baixos"
    "CN": "China",                # "República Popular da China"
    "IE": "Irlanda",              # "República da Irlanda"
    "PS": "Palestina",            # "Estado da Palestina"
    "MM": "Mianmar",              # "Birmânia" — a Wikipédia lusófona usa Mianmar
}

# Apelidos que a mesa fala e que o altLabel do Wikidata não tem. Sem isso,
# alguém digita "Holanda" e o jogo diz que errou.
APELIDOS = {
    "US": ["eua", "estados unidos da america"],
    "GB": ["inglaterra", "uk", "gra bretanha"],
    "AE": ["emirados arabes", "emirados"],
    "CD": ["congo democratico", "rd congo", "congo kinshasa", "zaire"],
    "CG": ["congo brazzaville", "republica do congo"],
    "CZ": ["republica tcheca", "tchequia"],
    "NL": ["holanda", "paises baixos"],
    "CI": ["costa do marfim", "marfim"],
    "TL": ["timor leste"],
    "MM": ["birmania"],
    "SZ": ["suazilandia"],
    "VA": ["vaticano", "santa se"],
    "PS": ["palestina"],
    "TW": ["taiwan", "formosa"],
    "MK": ["macedonia", "macedonia do norte"],
    "CV": ["cabo verde"],
    "KR": ["coreia do sul"],
    "KP": ["coreia do norte"],
    "GR": ["grecia"],
    "CH": ["suica"],
    "DK": ["dinamarca"],
    # Grafia que a mesa usa e que o rótulo em português não tem. À esquerda o
    # código, à direita o que alguém digitaria de verdade no celular.
    "BY": ["bielorrussia", "belarus"],
    "BH": ["bahrein", "barem"],
    "BF": ["burkina faso", "burquina fasso"],
    "BJ": ["benin"],
    "SC": ["seychelles", "seicheles"],
    "KI": ["kiribati", "quiribati"],
    "MD": ["moldova", "moldavia"],
    "BW": ["botsuana", "botswana"],
    "SM": ["sao marinho", "san marino"],
    "FK": ["malvinas", "falkland"],
    "CW": ["curacao", "curacau"],
    "CN": ["china", "republica popular da china"],
    "IE": ["irlanda", "eire"],
    "NL": ["holanda", "paises baixos"],
    "MM": ["birmania", "myanmar", "mianmar"],
    "SZ": ["suazilandia", "essuatini"],
    "TL": ["timor leste"],
    "ME": ["montenegro"],
    "LA": ["laos"],
    "VN": ["vietna", "vietnam"],
    "IR": ["ira", "irao"],
}

# Casos em que a fonte não responde direito e a gente diz por quê.
EXCECOES = {
    # A cadeira da Dinamarca na ONU está no item "Reino da Dinamarca"
    # (Q756617), que não tem código ISO — o código está em "Dinamarca" (Q35).
    # Sem esta linha o baralho teria 194 países em vez de 195.
    "DK": "pais",
    # XK não é código oficial da ISO: é o código de uso livre que a União
    # Europeia, o FMI e os bancos adotaram pro Kosovo. Entra como território
    # porque é um lugar com bandeira própria, e a carta diz o que ele é.
    "XK": "territorio",
}

# Cidade cujo rótulo do Wikidata não é o nome que a mesa fala. Q-id à esquerda
# porque rótulo muda; o nome antigo continua valendo como apelido.
CORRECOES_CIDADE = {
    "Q239":  "Bruxelas",   # o rótulo é "Cidade de Bruxelas", que é o município
    "Q3904": "Mbabane",    # o rótulo em português vem "Mebabane"
}

# Os dez lugares que têm mais de uma capital DE VERDADE — não é grafia
# diferente da mesma cidade (Bamaco/Bamako), são cidades diferentes. Todas
# valem o ponto, e a carta abre dizendo por que são várias. A ordem aqui é a
# ordem em que a carta lista. Escrito à mão porque o Wikidata guarda as três
# capitais da África do Sul sem dizer qual poder fica em qual — a informação
# que faz a carta valer alguma coisa não está na fonte.
CAPITAIS_MULTIPLAS = {
    "ZA": (["Pretória", "Cidade do Cabo", "Bloemfontein"],
           "A África do Sul tem três capitais, uma por poder: Pretória é a sede do "
           "Executivo, a Cidade do Cabo a do Parlamento e Bloemfontein a do "
           "Judiciário. As três valem."),
    "BO": (["Sucre", "La Paz"],
           "Sucre é a capital constitucional e sede do Judiciário; La Paz é a sede "
           "do governo e do Congresso. As duas valem."),
    "LK": (["Kotte", "Colombo"],
           "Sri Jayawardenepura Kotte é a capital oficial e sede do Parlamento; "
           "Colombo é a capital comercial e onde fica o Executivo. As duas valem."),
    "SZ": (["Mbabane", "Lobamba"],
           "Mbabane é a capital administrativa; Lobamba é a sede do parlamento e da "
           "monarquia. As duas valem."),
    "YE": (["Sana", "Áden"],
           "Sana é a capital constitucional e está sob controle houthi desde 2014; "
           "Áden é a sede do governo reconhecido internacionalmente. As duas valem."),
    "MY": (["Kuala Lumpur", "Putrajaya"],
           "Kuala Lumpur é a capital oficial, onde ficam o rei e o parlamento; "
           "Putrajaya é a capital administrativa, pra onde o governo federal se mudou "
           "em 1999. As duas valem."),
    "BJ": (["Porto Novo", "Cotonu"],
           "Porto Novo é a capital oficial e sede do parlamento; Cotonu é a sede do "
           "governo e a maior cidade do país. As duas valem."),
    "GS": (["Cabo Rei Eduardo", "Grytviken"],
           "King Edward Point é a base administrativa britânica na ilha; Grytviken é "
           "a antiga estação baleeira ao lado. O Wikidata lista as duas, e as duas "
           "valem."),
    "MS": (["Plymouth", "Brades"],
           "Plymouth continua sendo a capital oficial, mas está abandonada desde a "
           "erupção do vulcão Soufrière Hills, em 1997 — o governo funciona em "
           "Brades. As duas valem."),
    "PK": (["Islamabad", "Rawalpindi"],
           "Islamabad é a capital desde 1966. Rawalpindi foi a capital interina "
           "enquanto Islamabad era construída, e o Wikidata ainda a lista sem data "
           "de término; por isso ela também vale aqui."),
    "PS": (["Jerusalém Oriental", "Ramallah"],
           "A Palestina declara Jerusalém Oriental sua capital; Ramallah é a sede "
           "administrativa da Autoridade Palestina. O status da cidade é disputado. "
           "Todas valem."),
}


# Cidade que NÃO é a capital oficial mas é onde o governo senta de verdade.
# Quem responde isso não errou, e marcar como erro seria o jogo mentindo — a
# mesma regra das bandeiras gêmeas. O Wikidata não serve pra montar esta lista:
# ele deprecia Haia e Tel Aviv (marca como erradas) e nem lista Abidjã. Então é
# escrita à mão, e cada linha diz o fato que a torna aceitável.
QUASE = {
    "NL": [("Haia", "Amsterdã é a capital pela Constituição, mas o governo, o "
                    "parlamento e a Suprema Corte ficam em Haia.")],
    "IL": [("Tel Aviv", "Israel declara Jerusalém sua capital e é lá que ficam o "
                        "parlamento, o governo e a Suprema Corte. O status da cidade "
                        "é disputado, e a maior parte das embaixadas fica em Tel Aviv.")],
    "PS": [("Jerusalém", "A Palestina declara Jerusalém Oriental sua capital; o "
                         "status da cidade é disputado.")],
    "CI": [("Abidjã", "Iamussucro é a capital política desde 1983, mas o governo e "
                      "as embaixadas continuam em Abidjã.")],
    "TZ": [("Dar es Salaam", "Dodoma é a capital oficial desde 1996; boa parte do "
                             "governo e das embaixadas ficou em Dar es Salaam.")],
    "BI": [("Bujumbura", "Guitega virou a capital política em 2019; Bujumbura, que "
                         "era a capital, seguiu como capital econômica.")],
    "CL": [("Valparaíso", "Santiago é a capital, mas o Congresso Nacional se reúne "
                          "em Valparaíso desde 1990.")],
}


# Fora do baralho, com o motivo. Bandeira que não identifica um lugar sozinha
# não vira carta: a pessoa acertaria e o jogo diria que errou.
VETADOS = {
    "AQ": "a Antártica não tem bandeira oficial; o Wikidata traz a do Tratado",
    "BQ": "Bonaire, Santo Eustáquio e Saba não têm bandeira comum",
    "UM": "as Ilhas Menores dos EUA usam a bandeira americana",
}

# Códigos que a ISO não atribuiu a ninguém: são "excepcionalmente reservados"
# (AC, DG, TA, EA, IC...) ou de uso livre. Ficam de fora porque o universo do
# jogo é a lista oficial. A exceção documentada é o XK, lá em cima.
RESERVADOS = {"AC", "CP", "CQ", "DG", "EA", "EU", "EZ", "FX", "IC", "SU",
              "TA", "UK", "UN"}

# Bandeiras que são a mesma coisa na tela. Não dá pra pedir que alguém as
# distinga num celular: as duas respostas valem, e a carta explica a diferença.
GEMEAS = {
    ("ID", "MC"): "A Indonésia e Mônaco têm a mesma bandeira — vermelho sobre "
                  "branco. Muda só a proporção: 2:3 na Indonésia, 4:5 em Mônaco. "
                  "As duas respostas valem.",
    ("RO", "TD"): "A Romênia e o Chade têm o mesmo tricolor vertical. O azul do "
                  "Chade é um tom mais escuro, e é só isso — nem a ONU separou as "
                  "duas quando o Chade reclamou, em 2004. As duas respostas valem.",
}


# ---------------------------------------------------------------- utilidades

def norm(s):
    """minúscula, sem acento, sem pontuação — pra comparar palpite com resposta."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def get(url, params=None, chave=None, headers=None):
    """GET com cache em disco. chave = nome do arquivo no cache/."""
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, f"{chave}.json") if chave else None
    if caminho and os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    ultimo = None
    for tentativa in range(3):
        try:
            r = requests.get(url, params=params, timeout=180,
                             headers={"User-Agent": UA, **(headers or {})})
            if r.status_code == 404:      # artigo que não existe é resposta, não erro
                dados = None
                break
            r.raise_for_status()
            dados = r.json()
            break
        except Exception as e:
            ultimo = e
            time.sleep(4 * (tentativa + 1))
    else:
        raise RuntimeError(str(ultimo).split(" for url:")[0])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f)
    time.sleep(0.2)
    return dados


def sparql(query, chave):
    return get(SPARQL, {"query": query, "format": "json"}, chave,
               {"Accept": "application/sparql-results+json"})["results"]["bindings"]


def v(b, campo, padrao=None):
    return (b or {}).get(campo, {}).get("value", padrao)


# ---------------------------------------------------------------- consultas

# A proporção da bandeira (P2061) ficou de fora de propósito: o Wikidata mistura
# as convenções entre itens — a Romênia aparece como "2:3" e o Chade como "3:2"
# pra bandeira do mesmo formato. Número que não dá pra afirmar direito não vai
# pra carta. Onde a proporção importa de verdade, que é nas gêmeas, ela está
# escrita à mão em GEMEAS, conferida na especificação oficial de cada uma.
Q_BASE = """
SELECT ?e ?iso2 ?iso3 ?img ?adocao ?flagpt ?wpt ?sl WHERE {
  ?e wdt:P297 ?iso2 .
  FILTER NOT EXISTS { ?e wdt:P576 ?dissolvido }
  ?e wdt:P41 ?img .
  OPTIONAL { ?e wdt:P298 ?iso3 }
  OPTIONAL { ?e wdt:P163 ?flag .
             OPTIONAL { ?flag wdt:P571 ?adocao }
             OPTIONAL { ?fa schema:about ?flag ;
                            schema:isPartOf <https://pt.wikipedia.org/> ;
                            schema:name ?flagpt } }
  OPTIONAL { ?a schema:about ?e ; schema:isPartOf <https://pt.wikipedia.org/> ;
                schema:name ?wpt }
  ?e wikibase:sitelinks ?sl .
}
"""

# Membro DA ONU HOJE: tem a declaração e ela não tem data de término. Sem o
# filtro de término a Taiwan entraria — ela foi membro até 1971.
Q_ONU = """
SELECT ?iso2 WHERE {
  ?e wdt:P297 ?iso2 ; p:P463 ?st .
  ?st ps:P463 wd:Q1065 .
  FILTER NOT EXISTS { ?st pq:P582 ?fim }
}
"""

Q_NOMES = """
SELECT ?iso2 ?ptbr ?pt ?en ?wpt (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?apelidos) WHERE {
  ?e wdt:P297 ?iso2 .
  FILTER NOT EXISTS { ?e wdt:P576 ?dissolvido }
  OPTIONAL { ?e rdfs:label ?ptbr FILTER(LANG(?ptbr) = "pt-br") }
  OPTIONAL { ?e rdfs:label ?pt   FILTER(LANG(?pt)   = "pt")    }
  OPTIONAL { ?e rdfs:label ?en   FILTER(LANG(?en)   = "en")    }
  OPTIONAL { ?a schema:about ?e ; schema:isPartOf <https://pt.wikipedia.org/> ;
                schema:name ?wpt }
  OPTIONAL { ?e skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt-br", "pt")) }
}
GROUP BY ?iso2 ?ptbr ?pt ?en ?wpt
"""

# A língua vem junto: o desempate alfabético entre "América do Norte" (pt-BR) e
# outra grafia escolheria a errada. Capital não está aqui — ela tem consulta
# própria, porque precisa de Q-id, rank e data de término pra sair certa.
Q_FATOS = """
SELECT ?iso2 ?cont (LANG(?cont) AS ?cont_l) ?pop WHERE {
  ?e wdt:P297 ?iso2 .
  FILTER NOT EXISTS { ?e wdt:P576 ?dissolvido }
  OPTIONAL { ?e wdt:P30 ?ct . ?ct rdfs:label ?cont FILTER(LANG(?cont) IN ("pt-br","pt")) }
  OPTIONAL { ?e wdt:P1082 ?pop }
}
"""

# Capital por Q-ID, não por nome: "Bamaco" e "Bamako" são rótulos da MESMA
# cidade, e agrupar por texto faria o Mali parecer ter duas capitais. Também
# traz o rank e a data de término, porque a Nigéria tem Lagos até 1991 e Abuja
# como preferencial — sem isso a capital certa se perde no meio.
Q_CAPITAIS = """
SELECT ?iso2 ?cap ?rank ?fim ?ptbr ?pt ?en ?wpt
       (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?apelidos) WHERE {
  ?e wdt:P297 ?iso2 .
  FILTER NOT EXISTS { ?e wdt:P576 ?dissolvido }
  ?e p:P36 ?st . ?st ps:P36 ?cap . ?st wikibase:rank ?rank .
  OPTIONAL { ?st pq:P582 ?fim }
  OPTIONAL { ?cap rdfs:label ?ptbr FILTER(LANG(?ptbr) = "pt-br") }
  OPTIONAL { ?cap rdfs:label ?pt   FILTER(LANG(?pt)   = "pt")    }
  OPTIONAL { ?cap rdfs:label ?en   FILTER(LANG(?en)   = "en")    }
  OPTIONAL { ?a schema:about ?cap ; schema:isPartOf <https://pt.wikipedia.org/> ;
                schema:name ?wpt }
  OPTIONAL { ?cap skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt-br", "pt")) }
}
GROUP BY ?iso2 ?cap ?rank ?fim ?ptbr ?pt ?en ?wpt
"""

CONTINENTES = {
    "África": "África",
    "Europa": "Europa",
    "Ásia": "Ásia",
    "Oceania": "Oceania",
    "América do Sul": "América do Sul",
    "América do Norte": "América do Norte e Central",
    "América do Norte e América Central": "América do Norte e Central",
    "América Central": "América do Norte e Central",
    "Antártida": "Antártida",
    "Insulíndia": "Ásia",
}


def melhor(pares):
    """[(lang, texto)] -> o texto em pt-br se houver, senão em pt."""
    for alvo in ("pt-br", "pt"):
        for lang, txt in pares:
            if lang == alvo:
                return txt
    return pares[0][1] if pares else None


def coleta():
    onu = {v(b, "iso2") for b in sparql(Q_ONU, "wd_onu")}
    nomes = {v(b, "iso2"): b for b in sparql(Q_NOMES, "wd_nomes")}

    fatos = defaultdict(lambda: {"cont": [], "pop": []})
    for b in sparql(Q_FATOS, "wd_fatos3"):
        f = fatos[v(b, "iso2")]
        if v(b, "cont"):
            f["cont"].append((v(b, "cont_l"), CONTINENTES.get(v(b, "cont"), v(b, "cont"))))
        if v(b, "pop"):
            f["pop"].append(int(float(v(b, "pop"))))

    por_iso = defaultdict(dict)
    for b in sparql(Q_BASE, "wd_base2"):
        iso2 = v(b, "iso2")
        d = por_iso[iso2]
        d.setdefault("qid", v(b, "e", "").rsplit("/", 1)[-1])
        d.setdefault("sitelinks", int(v(b, "sl", 0)))
        d.setdefault("imgs", set()).add(v(b, "img"))
        for campo in ("iso3", "adocao", "flagpt", "wpt"):
            if v(b, campo):
                d.setdefault(campo, v(b, campo))
    return por_iso, onu, nomes, fatos


def arquivo_da(url):
    return requests.utils.unquote(url.rsplit("/", 1)[-1])


def escolhe_imagem(imgs):
    """
    Mais de um P41: fica o arquivo de nome mais curto e canônico. Guadalupe tem
    "Flag of France.svg" e "Flag of Guadeloupe (Local).svg"; a primeira ganha e
    aí a regra de bandeira repetida manda Guadalupe embora, que é o certo — a
    bandeira local não é oficial.
    """
    return sorted(imgs, key=lambda u: (len(arquivo_da(u)), arquivo_da(u)))[0]


def nome_de(iso2, b):
    if iso2 in CORRECOES:
        return CORRECOES[iso2]
    for campo in ("ptbr", "pt", "wpt", "en"):
        nome = v(b, campo)
        if nome:
            # alguns rótulos vêm em caixa baixa ("ilhas Cook"); a carta é título
            return nome[0].upper() + nome[1:]
    return None


def resumo(titulo, prefixo="wp"):
    """Primeiras frases de um artigo da Wikipédia lusófona, com o link."""
    chave = prefixo + "_" + re.sub(r"[^A-Za-z0-9]+", "_", titulo)[:70]
    d = get(WIKI_PT + requests.utils.quote(titulo.replace(" ", "_"), safe=""), None, chave)
    if not d or not d.get("extract"):
        return None, None
    texto = re.sub(r"\s+", " ", d["extract"]).strip()
    frases, saida = re.split(r"(?<=[.!?]) ", texto), ""
    for f in frases:
        if saida and len(saida) + len(f) > 400:
            break
        saida = (saida + " " + f).strip()
    link = (d.get("content_urls", {}).get("desktop", {}).get("page")
            or "https://pt.wikipedia.org/wiki/" + titulo.replace(" ", "_"))
    return saida, link


def janela_de_leitura():
    """Os 12 meses fechados mais recentes."""
    hoje = date.today()
    fim = date(hoje.year, hoje.month, 1)
    ini = date(fim.year - 1, fim.month, 1)
    ultimo = (date(fim.year, fim.month, 1).toordinal() - 1)
    return (ini.strftime("%Y%m0100"), date.fromordinal(ultimo).strftime("%Y%m%d00"),
            f"{ini:%m/%Y} a {date.fromordinal(ultimo):%m/%Y}")


def leitura_do_artigo(titulo, ini, fim):
    """
    Quantas vezes o artigo do país foi lido na Wikipédia em português. É a régua
    de "mais fácil": mede o quanto a nossa língua olha pra aquele país. Não é
    dificuldade da bandeira — a tela do jogo diz isso com todas as letras.
    """
    chave = "pv_" + re.sub(r"[^A-Za-z0-9]+", "_", titulo)[:70]
    d = get(PAGEVIEWS.format(titulo=requests.utils.quote(titulo.replace(" ", "_"), safe=""),
                             ini=ini, fim=fim), None, chave)
    if not d or not d.get("items"):
        return None
    return sum(i.get("views", 0) for i in d["items"])


def coleta_capitais():
    """
    iso2 -> [{qid, nome, apelidos, artigo}], só as capitais de HOJE.

    Três regras aqui, cada uma consertando um erro que apareceu de verdade:

    - agrupar por Q-id, não por nome: "Bamaco" e "Bamako" são rótulos da mesma
      cidade, e agrupar por texto fazia o Mali parecer ter duas capitais;
    - jogar fora declaração com data de término: Lagos foi capital da Nigéria
      até 1991 e continua no item;
    - onde existe rank preferencial, só ele vale — é o que faz sobrar Abuja.

    Cada rótulo que a cidade tem em português vira apelido, então quem digita
    "Bamako", "Moscovo" ou "Banguecoque" acerta.
    """
    bruto = defaultdict(dict)
    for b in sparql(Q_CAPITAIS, "wd_capitais2"):
        if v(b, "fim"):
            continue
        rank = (v(b, "rank") or "").rsplit("#", 1)[-1]
        if rank == "DeprecatedRank":
            continue
        qid = v(b, "cap", "").rsplit("/", 1)[-1]
        nome = CORRECOES_CIDADE.get(qid) or (
            v(b, "ptbr") or v(b, "pt") or v(b, "wpt") or v(b, "en"))
        if not nome:
            continue
        apelidos = {norm(nome)}
        for campo in ("ptbr", "pt", "wpt", "en"):
            if v(b, campo):
                apelidos.add(norm(v(b, campo)))
        for a in (v(b, "apelidos", "") or "").split("|"):
            if len(norm(a)) > 2:
                apelidos.add(norm(a))
        bruto[v(b, "iso2")][qid] = {
            "qid": qid, "nome": nome[0].upper() + nome[1:],
            "apelidos": sorted(apelidos), "artigo": v(b, "wpt"), "rank": rank}

    saida, avisos = {}, []
    for iso2, caps in bruto.items():
        # Rank preferencial ORDENA, não exclui. Ele diz qual a capital que a
        # carta lê primeiro (Abuja, Amsterdã), mas a outra continua sendo uma
        # resposta que a mesa daria — Haia e Tel Aviv são disso. O que sai
        # mesmo é capital de antigamente, e isso já saiu pela data de término.
        lista = sorted(caps.values(), key=lambda c: c["rank"] != "PreferredRank")
        ordem = CAPITAIS_MULTIPLAS.get(iso2, (None, None))[0]
        if ordem:
            # a mão diz a ordem; se um nome não bate mais, o gerador reclama em
            # vez de fingir que está tudo certo
            pos = {norm(n): i for i, n in enumerate(ordem)}
            for c in lista:
                if norm(c["nome"]) not in pos:
                    avisos.append(f"{iso2}: '{c['nome']}' não está em CAPITAIS_MULTIPLAS")
            for n in ordem:
                if not any(norm(n) == norm(c["nome"]) for c in lista):
                    avisos.append(f"{iso2}: '{n}' está em CAPITAIS_MULTIPLAS mas sumiu do Wikidata")
            lista.sort(key=lambda c: pos.get(norm(c["nome"]), 99))
        elif len(lista) > 1:
            avisos.append(f"{iso2}: {len(lista)} capitais e nenhuma explicação escrita")
        for c in lista:
            c.pop("rank")
        saida[iso2] = lista
    return saida, avisos


def baixa_bandeira(iso2, arquivo):
    """PNG renderizado do SVG do Commons. Fica no repositório: o jogo é offline."""
    os.makedirs(IMG, exist_ok=True)
    destino = os.path.join(IMG, f"{iso2.lower()}.png")
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return False
    r = requests.get(COMMONS + requests.utils.quote(arquivo, safe=""),
                     params={"width": LARGURA}, timeout=180, headers={"User-Agent": UA})
    r.raise_for_status()
    with open(destino, "wb") as f:
        f.write(r.content)
    time.sleep(0.2)
    return True


def encolhe(caminhos):
    """
    pngquant: 24 bits viram paleta de 256 cores. Bandeira é cor chapada, então
    a diferença não aparece na tela e o repositório fica com um terço do peso.
    Se o pngquant não estiver instalado, segue com o PNG original.
    """
    try:
        subprocess.run(["pngquant", "--version"], capture_output=True, check=True)
    except Exception:
        print("  (pngquant não instalado — as imagens ficam no tamanho original)")
        return 0
    antes = sum(os.path.getsize(c) for c in caminhos)
    subprocess.run(["pngquant", "--force", "--skip-if-larger", "--quality=70-96",
                    "--ext", ".png", *caminhos], capture_output=True)
    depois = sum(os.path.getsize(c) for c in caminhos)
    return antes - depois


# ---------------------------------------------------------------- montagem

def main():
    por_iso, onu, nomes, fatos = coleta()
    capitais, avisos = coleta_capitais()
    print(f"Wikidata: {len(por_iso)} códigos com bandeira, {len(onu)} membros da ONU, "
          f"{len(capitais)} com capital")

    # Bandeira repetida não vira duas cartas: fica o país soberano e o
    # território sai. Sem isso a Ilha Bouvet seria "erro" pra quem digitasse
    # Noruega olhando a bandeira da Noruega.
    dono = defaultdict(list)
    for iso2, d in por_iso.items():
        d["arquivo"] = arquivo_da(escolhe_imagem(d["imgs"]))
        dono[d["arquivo"]].append(iso2)

    ini, fim, janela = janela_de_leitura()
    print(f"leitura na Wikipédia em português: {janela}")

    cortes, cartas = [], []
    for iso2 in sorted(por_iso):
        d = por_iso[iso2]
        if iso2 in VETADOS:
            cortes.append((iso2, VETADOS[iso2]))
            continue
        if iso2 in RESERVADOS:
            cortes.append((iso2, "código ISO reservado, não atribuído a ninguém"))
            continue
        irmaos = dono[d["arquivo"]]
        if len(irmaos) > 1:
            soberanos = [i for i in irmaos if i in onu]
            if iso2 not in soberanos:
                quem = soberanos[0] if soberanos else irmaos[0]
                cortes.append((iso2, "usa a mesma bandeira de "
                               f"{nome_de(quem, nomes.get(quem)) or quem} ({quem})"))
                continue

        nome = nome_de(iso2, nomes.get(iso2))
        if not nome:
            cortes.append((iso2, "sem nome em português no Wikidata"))
            continue

        f = fatos.get(iso2, {})
        tipo = EXCECOES.get(iso2) or (
            "pais" if (iso2 in onu or iso2 in ("VA", "PS")) else "territorio")

        apelidos = {norm(nome)}
        for a in (v(nomes.get(iso2), "apelidos", "") or "").split("|"):
            if len(norm(a)) > 2:
                apelidos.add(norm(a))
        apelidos.update(norm(a) for a in APELIDOS.get(iso2, []))

        nota, link = resumo(d["flagpt"]) if d.get("flagpt") else (None, None)
        caps = capitais.get(iso2, [])
        nota_cap, link_cap = (resumo(caps[0]["artigo"], "cid")
                              if caps and caps[0].get("artigo") else (None, None))
        artigo = d.get("wpt") or v(nomes.get(iso2), "wpt")
        cartas.append({
            "iso2": iso2, "iso3": d.get("iso3"), "qid": d["qid"], "tipo": tipo,
            "nome": nome, "apelidos": sorted(apelidos),
            "continente": melhor(f.get("cont") or []),
            "capitais": [{k: c[k] for k in ("qid", "nome", "apelidos")} for c in caps],
            "capital": caps[0]["nome"] if caps else None,
            "nota_capital": nota_cap, "link_capital": link_cap,
            "varias_capitais": CAPITAIS_MULTIPLAS.get(iso2, (None, None))[1],
            "quase": [{"nome": n, "apelidos": sorted({norm(n)}), "explica": e}
                      for n, e in QUASE.get(iso2, [])],
            "populacao": max(f.get("pop") or [0]) or None,
            "adocao": (d.get("adocao") or "")[:10] or None,
            "arquivo": d["arquivo"], "img": f"img/{iso2.lower()}.png",
            "nota": nota, "link": link, "artigo": artigo,
            "leitura": leitura_do_artigo(artigo, ini, fim) if artigo else None,
            "sitelinks": d["sitelinks"],
        })

    # Uma capital que serve a mais de um lugar não vira carta do módulo "de que
    # país é esta capital": Jerusalém aparece em Israel e na Palestina, e a
    # carta teria duas respostas certas por um motivo que não é geografia.
    de_quem = defaultdict(set)
    for c in cartas:
        for cap in c["capitais"]:
            de_quem[norm(cap["nome"])].add(c["iso2"])
    for c in cartas:
        for cap in c["capitais"]:
            donos = de_quem[norm(cap["nome"])]
            if len(donos) > 1:
                cap["ambigua"] = sorted(donos)

    # Bandeiras iguais na tela: cada uma aceita a outra como resposta.
    porcarta = {c["iso2"]: c for c in cartas}
    for (a, b), explica in GEMEAS.items():
        if a in porcarta and b in porcarta:
            porcarta[a]["gemea"] = {"iso2": b, "nome": porcarta[b]["nome"], "explica": explica}
            porcarta[b]["gemea"] = {"iso2": a, "nome": porcarta[a]["nome"], "explica": explica}

    # ------------------------------------------------------------- imagens
    novas, caminhos = 0, []
    for c in list(cartas):
        try:
            novas += baixa_bandeira(c["iso2"], c["arquivo"])
            caminhos.append(os.path.join(IMG, f"{c['iso2'].lower()}.png"))
        except Exception as e:
            cortes.append((c["iso2"], f"a bandeira não baixou: {e}"))
            cartas.remove(c)
    poupado = encolhe(caminhos)

    # sobra do baralho anterior: arquivo de quem saiu não fica pra trás
    validos = {c["iso2"].lower() + ".png" for c in cartas}
    for arq in sorted(os.listdir(IMG)):
        if arq.endswith(".png") and arq not in validos:
            os.remove(os.path.join(IMG, arq))
            print(f"  removido {IMG}/{arq} (não está mais no baralho)")

    paises = [c for c in cartas if c["tipo"] == "pais"]
    banco = {
        "gerado_em": time.strftime("%Y-%m-%d"),
        "universo": "ISO 3166-1 alpha-2",
        "janela_leitura": janela,
        "cartas": sorted(cartas, key=lambda c: -(c["leitura"] or 0)),
    }
    with open("banco.json", "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=1)

    peso = sum(os.path.getsize(os.path.join(IMG, a)) for a in os.listdir(IMG))
    print(f"\n{len(cartas)} cartas: {len(paises)} países + {len(cartas)-len(paises)} territórios")
    print(f"bandeiras: {novas} novas, {peso/1e6:.1f} MB no total "
          f"({poupado/1e6:.1f} MB poupados pelo pngquant)")
    print(f"com nota da Wikipédia: {sum(1 for c in cartas if c['nota'])}")
    print(f"com data de adoção:    {sum(1 for c in cartas if c['adocao'])}")
    print(f"com leitura medida:    {sum(1 for c in cartas if c['leitura'])}")
    comcap = [c for c in cartas if c["capitais"]]
    print(f"com capital:           {len(comcap)} "
          f"({sum(1 for c in comcap if len(c['capitais']) > 1)} com mais de uma)")
    print(f"com nota da capital:   {sum(1 for c in cartas if c['nota_capital'])}")
    print(f"capital ambígua:       "
          f"{sorted({cap['nome'] for c in cartas for cap in c['capitais'] if cap.get('ambigua')})}")
    print(f"pares de gêmeas:       {sum(1 for c in cartas if c.get('gemea'))//2}")
    if avisos:
        print(f"\nconferir as capitais escritas à mão ({len(avisos)}):")
        for a in avisos:
            print("  -", a)
    if cortes:
        print(f"\nfora do baralho ({len(cortes)}):")
        for iso2, motivo in sorted(cortes):
            print(f"  {iso2}: {motivo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
