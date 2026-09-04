# -*- coding: utf-8 -*-
"""
Cartas do tema "cinema", do Wikidata.

Bilheteria é a propriedade P2142, filtrada em dólar (Q4917) — sem esse filtro
entram valores em iene e em rupia e o ranking vira salada. O ano do filme é o
MENOR ano de P577: um filme tem uma data de estreia por país, e sem o MIN o
Jurassic Park aparece duas vezes na mesma carta.

Fica de fora: carta por gênero. O P136 do Wikidata é etiqueta frouxa — o top
de "terror" veio com Gravidade e Doutor Estranho no Multiverso da Loucura, que
a mesa desmentiria na hora.

Fica de fora também, por enquanto: prêmios. A hierarquia de categorias do Oscar no
Wikidata não é direta e a contagem sai errada — melhor não ter a carta do que
ter uma que a mesa desminta.
"""

from wikidata import nome_de, item, carta, indexa

FILME = "wd:Q11424"


def _fmt_usd(v):
    if v >= 1e9:
        return f"US$ {v/1e9:.2f} bi".replace(".", ",")
    return f"US$ {v/1e6:.0f} mi"


def _bilheteria(sparql, norm, problemas, chave_cache, filtro="", piso=100000000):
    q = f"""
    SELECT ?f ?ano ?bil ?f_nome
           (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?f_apelidos) WHERE {{
      {{ SELECT ?f (MIN(YEAR(?d)) AS ?ano) (MAX(?b) AS ?bil) WHERE {{
           ?f wdt:P31 {FILME} ; wdt:P577 ?d ; p:P2142 ?s .
           ?s ps:P2142 ?b ; psv:P2142/wikibase:quantityUnit wd:Q4917 .
           FILTER(?b > {piso})
         }} GROUP BY ?f }}
      {filtro}
      OPTIONAL {{ ?f skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt","pt-br")) }}
      {nome_de('f')}
    }} GROUP BY ?f ?ano ?bil ?f_nome ORDER BY DESC(?bil) LIMIT 25
    """
    try:
        d = sparql(q, chave_cache)
    except Exception as e:
        problemas.append(f"cinema/{chave_cache}: {e}")
        return []
    saida, sem_nome = [], 0
    for b in d["results"]["bindings"]:
        it = item(b, "f", norm)
        if not it:
            sem_nome += 1
            continue
        saida.append((*it, float(b["bil"]["value"])))
    if sem_nome:
        problemas.append(f"cinema/{chave_cache}: {sem_nome} filme(s) sem nome — "
                         "carta descartada, resposta sem nome não dá pra jogar")
        return []
    return saida


def cartas_de_cinema(sparql, norm, problemas):
    cartas, listas = [], {"filme": [], "pessoa": []}
    NOTA = ("Bilheteria mundial acumulada, em dólar corrente — sem corrigir "
            "inflação, então filme antigo aparece menor do que foi. Reestreia "
            "conta junto.")

    # piso alto no ranking geral: sem ele a query varre o catálogo inteiro
    # e o servidor do Wikidata devolve 504
    it = _bilheteria(sparql, norm, problemas, "cine_geral", piso=900000000)
    if it:
        listas["filme"].append(it)
        cartas.append(carta("Quais os filmes de maior bilheteria de todos os tempos?",
                            "Wikidata", "bilheteria mundial", it, len(it),
                            "filme", "Cinema", NOTA, _fmt_usd, "cinema"))

    for ini, fim, rotulo in ((1980, 1989, "anos 80"), (1990, 1999, "anos 90"),
                             (2000, 2009, "anos 2000"), (2010, 2019, "anos 2010"),
                             (2020, 2029, "anos 2020")):
        it = _bilheteria(sparql, norm, problemas, f"cine_{ini}",
                         f"FILTER(?ano >= {ini} && ?ano <= {fim})",
                         piso=200000000 if ini < 2000 else 400000000)
        if it:
            listas["filme"].append(it)
            c = carta(f"Quais os filmes de maior bilheteria dos {rotulo}?",
                      "Wikidata", "bilheteria mundial", it, len(it), "filme",
                      "Cinema", NOTA + " O ano é o da primeira estreia.",
                      _fmt_usd, "cinema")
            if c:
                cartas.append(c)


    # ---------------------------------------------------------- diretores
    # A soma TEM que fechar antes de encostar em rótulo e apelido. Se o
    # OPTIONAL de altLabel entrar junto, cada filme conta uma vez por apelido
    # do diretor e o total infla — foi assim que o Tim Burton apareceu com
    # 8,5 bi em vez de 4,5.
    q = f"""
    SELECT ?dir ?dir_nome ?total ?n
           (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?dir_apelidos) WHERE {{
      {{ SELECT ?dir (SUM(?bil) AS ?total) (COUNT(DISTINCT ?f) AS ?n) WHERE {{
           {{ SELECT ?f ?dir (MAX(?b) AS ?bil) WHERE {{
                ?f wdt:P31 {FILME} ; wdt:P57 ?dir ; p:P2142 ?s .
                ?s ps:P2142 ?b ; psv:P2142/wikibase:quantityUnit wd:Q4917 .
                ?dir wdt:P31 wd:Q5 .
              }} GROUP BY ?f ?dir }}
         }} GROUP BY ?dir }}
      OPTIONAL {{ ?dir skos:altLabel ?alt FILTER(LANG(?alt) IN ("pt","pt-br")) }}
      {nome_de('dir')}
    }} GROUP BY ?dir ?dir_nome ?total ?n ORDER BY DESC(?total) LIMIT 25
    """
    try:
        d = sparql(q, "cine_diretores")
        itens, sem_nome = [], 0
        for b in d["results"]["bindings"]:
            i = item(b, "dir", norm)
            if not i:
                sem_nome += 1
                continue
            itens.append((*i, float(b["total"]["value"])))
        if sem_nome:
            problemas.append("cinema/diretores: item sem nome, carta descartada")
        elif itens:
            c = carta("Quais os diretores cujos filmes mais faturaram?",
                      "Wikidata", "bilheteria somada", itens, len(itens),
                      "pessoa", "Cinema",
                      "Soma da bilheteria de todos os filmes que a pessoa dirigiu. "
                      "Quem dirige pouco e grande passa quem dirige muito e médio.",
                      _fmt_usd, "cinema")
            if c:
                cartas.append(c)
                listas["pessoa"].append(itens)
    except Exception as e:
        problemas.append(f"cinema/diretores: {e}")

    return cartas, indexa(listas)
