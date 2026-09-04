# -*- coding: utf-8 -*-
"""
Cartas do tema "esporte", do Wikidata.

Aqui a lição foi cara: contagem de título só vale se a série de edições estiver
inteira. O Campeonato Brasileiro no Wikidata não tem 1964, 2000, 2005, 2020,
2023 e 2024 — com isso o Palmeiras saía com 11 títulos e o Corinthians com 6,
e qualquer brasileiro na mesa desmentiria a carta. Copa do Brasil e Paulista
param em 2020; o Carioca tem seis buracos.

Por isso `titulos()` confere a série antes de montar a carta e recusa quando
falta ano. Hoje só a Libertadores passa. Se alguém completar o Wikidata, as
outras entram sozinhas — é só acrescentar em COMPETICOES.

Capacidade de estádio (P1083) tem valor histórico junto: o Morumbi aparece com
120 mil, que é a lotação dos anos 70. Daí o filtro de data-fim e de rank
depreciado.
"""

import re

from wikidata import nome_de, item, carta, indexa

COMPETICOES = [
    # (Q-id, nome na pergunta, primeiro ano esperado)
    ("Q184795", "a Copa Libertadores", 1960),
    ("Q206813", "o Campeonato Brasileiro", 1959),
    ("Q843989", "a Copa do Brasil", 1989),
    ("Q1348155", "o Campeonato Paulista", 1902),
    ("Q765749", "o Campeonato Carioca", 1906),
]

# Um ano depois do último que a competição realmente teve; se a série do
# Wikidata parar antes disso, os títulos recentes estão faltando.
ATUAL = 2025


def _fmt_titulos(v):
    return f"{int(v)} título{'s' if v != 1 else ''}"


def _fmt_lugares(v):
    return f"{int(v):,}".replace(",", ".") + " lugares"


def _serie_completa(anos, primeiro):
    """Sem buraco no meio e chegando até hoje? Senão a contagem mente."""
    if not anos:
        return "nenhuma edição encontrada"
    faltam = [a for a in range(min(anos), max(anos) + 1) if a not in anos]
    if faltam:
        return f"faltam as edições de {', '.join(map(str, faltam[:8]))}"
    if max(anos) < ATUAL - 1:
        return f"a série para em {max(anos)}, então falta título recente"
    if min(anos) > primeiro + 1:
        return f"a série começa em {min(anos)}, mas a competição é de {primeiro}"
    return None


def _titulos(sparql, norm, problemas, qid, rotulo, primeiro):
    q = f"""
    SELECT ?c ?c_nome ?edLabel
           (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?c_apelidos) WHERE {{
      ?ed wdt:P3450 wd:{qid} ; wdt:P1346 ?c .
      ?ed rdfs:label ?edLabel . FILTER(LANG(?edLabel) = "pt")
      OPTIONAL {{ ?c skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt","pt-br")) }}
      {nome_de('c')}
    }} GROUP BY ?c ?c_nome ?edLabel
    """
    try:
        d = sparql(q, f"esp_tit_{qid}")
    except Exception as e:
        problemas.append(f"esporte/{qid}: {e}")
        return None

    linhas = d["results"]["bindings"]
    anos = {int(m.group()) for b in linhas
            if (m := re.search(r"\d{4}", b["edLabel"]["value"]))}
    problema = _serie_completa(anos, primeiro)
    if problema:
        problemas.append(f"esporte: {rotulo} descartado — {problema}. "
                         "Contagem de título com edição faltando sai errada.")
        return None

    por_clube = {}
    for b in linhas:
        i = item(b, "c", norm)
        if not i:
            problemas.append(f"esporte/{rotulo}: campeão sem nome, carta descartada")
            return None
        chave, nome, apelidos = i
        if chave not in por_clube:
            por_clube[chave] = [chave, nome, apelidos, 0]
        por_clube[chave][3] += 1

    itens = sorted(por_clube.values(), key=lambda x: -x[3])
    return [tuple(x) for x in itens], len(anos)


def _estadios(sparql, norm, problemas, chave, onde_sparql, rotulo):
    q = f"""
    SELECT ?e ?e_nome (MAX(?cap) AS ?c)
           (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?e_apelidos) WHERE {{
      ?e wdt:P31/wdt:P279* wd:Q483110 .
      {onde_sparql}
      ?e p:P1083 ?st . ?st ps:P1083 ?cap .
      FILTER NOT EXISTS {{ ?st pq:P582 ?fim }}
      FILTER NOT EXISTS {{ ?st wikibase:rank wikibase:DeprecatedRank }}
      OPTIONAL {{ ?e skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt","pt-br")) }}
      {nome_de('e')}
    }} GROUP BY ?e ?e_nome ORDER BY DESC(?c) LIMIT 25
    """
    try:
        d = sparql(q, chave)
    except Exception as e:
        problemas.append(f"esporte/{chave}: {e}")
        return []
    itens = []
    for b in d["results"]["bindings"]:
        i = item(b, "e", norm)
        if not i:
            problemas.append(f"esporte/{rotulo}: estádio sem nome, carta descartada")
            return []
        itens.append((*i, float(b["c"]["value"])))
    return itens


def cartas_de_esporte(sparql, norm, problemas):
    cartas, listas = [], {"clube": [], "estadio": []}

    for qid, rotulo, primeiro in COMPETICOES:
        r = _titulos(sparql, norm, problemas, qid, rotulo, primeiro)
        if not r:
            continue
        itens, n_edicoes = r
        listas["clube"].append(itens)
        c = carta(f"Quais os clubes que mais venceram {rotulo}?",
                  "Wikidata", "títulos", itens, len(itens), "clube", "Esporte",
                  f"Contagem das {n_edicoes} edições, da primeira até hoje. "
                  "O gerador confere se falta algum ano antes de montar a "
                  "carta — contagem de título com buraco sai errada.",
                  _fmt_titulos, "esporte")
        if c:
            cartas.append(c)

    for chave, onde, rotulo, pergunta in (
        ("esp_est_br", "?e wdt:P17 wd:Q155 .", "estádios do Brasil",
         "Quais os maiores estádios do Brasil?"),
        ("esp_est_mundo", "", "estádios do mundo",
         "Quais os maiores estádios do mundo?"),
    ):
        itens = _estadios(sparql, norm, problemas, chave, onde, rotulo)
        if itens:
            listas["estadio"].append(itens)
            c = carta(pergunta, "Wikidata", "capacidade", itens, len(itens),
                      "estadio", "Esporte",
                      "Capacidade atual, sem contar lotação de outra época — o "
                      "Morumbi já coube 120 mil, hoje cabe bem menos. O nome no "
                      "gabarito é o oficial; o apelido também vale no palpite.",
                      _fmt_lugares, "esporte")
            if c:
                cartas.append(c)

    return cartas, indexa(listas)
