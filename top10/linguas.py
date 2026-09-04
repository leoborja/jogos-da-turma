# -*- coding: utf-8 -*-
"""
Cartas do tema "línguas".

Fontes:
  Glottolog (CLDF)  catálogo acadêmico de línguas do mundo — quantas línguas
                    se fala em cada país, quantas línguas tem cada família.
                    Contável e conferível, é o que a gente usa.
  Wikidata (P37)    língua oficial de cada país.

O que ficou DE FORA de propósito:
  - "línguas com mais falantes": o P1098 do Wikidata mistura macro-língua com
    língua (zho x cmn, ara x arb) e falante nativo com falante total. Número
    duvidoso quebra o jogo, então essa carta só entra escrita à mão com fonte.
  - "países com mais línguas oficiais": a cobertura do P37 é irregular
    (a Bolívia aparece com 4 e a constituição dela lista 37).
  - "línguas faladas em mais países": o Glottolog conta cada variedade do
    romani como língua separada, então o top 10 vira quatro romanis seguidos.
"""

import csv
import io
from collections import Counter, defaultdict

GLOTTOLOG_CSV = ("https://raw.githubusercontent.com/glottolog/"
                 "glottolog-cldf/master/cldf/languages.csv")

# "famílias" que o Glottolog usa como gaveta interna, não são famílias de verdade
PSEUDO_FAMILIAS = {"Bookkeeping", "Unclassifiable", "Sign Language",
                   "Unattested", "Pidgin", "Mixed Language", "Artificial Language",
                   "Speech Register"}

FAMILIAS_PT = {
    "Atlantic-Congo": "Atlântico-Congo",
    "Austronesian": "Austronésia",
    "Indo-European": "Indo-europeia",
    "Sino-Tibetan": "Sino-tibetana",
    "Afro-Asiatic": "Afro-asiática",
    "Nuclear Trans New Guinea": "Trans-Nova Guiné Nuclear",
    "Pama-Nyungan": "Pama-Nyungan",
    "Otomanguean": "Oto-mangue",
    "Austroasiatic": "Austro-asiática",
    "Tai-Kadai": "Tai-Kadai",
    "Dravidian": "Dravídica",
    "Turkic": "Turcomana",
    "Uralic": "Urálica",
    "Tupian": "Tupi",
    "Arawakan": "Aruaque",
    "Nilotic": "Nilótica",
    "Mande": "Mandê",
    "Sepik": "Sepik",
    "Salishan": "Salish",
    "Uto-Aztecan": "Uto-asteca",
    "Quechuan": "Quíchua",
    "Mongolic-Khitan": "Mongólica",
    "Japonic": "Japônica",
    "Koreanic": "Coreana",
    "Nakh-Daghestanian": "Nakh-daguestanesa",
    "Cariban": "Caribe",
    "Chibchan": "Chibcha",
    "Algic": "Álgica",
    "Maipurean": "Maipure",
    "Ta-Ne-Omotic": "Omótica",
    "Central Sudanic": "Sudânica Central",
    "Songhay": "Songai",
    "Kadu": "Kadu",
}


def carta(pergunta, fonte, unidade, itens, universo, tipo, escopo="mundo",
          nota=None, tol=0.001):
    """Monta uma carta a partir de [(nome, valor, apelidos, iso3?), ...] já ordenado."""
    if len(itens) < 11:
        return None
    dez, onze = itens[:10], itens[10]
    a, b = abs(dez[-1][1]), abs(onze[1])
    respostas = []
    for i, it in enumerate(dez):
        ehPais = len(it) > 3 and bool(it[3])
        r = {"pos": i + 1, "chave": it[3] if ehPais else it[0],
             "nome": it[0], "valor": it[1],
             "valor_fmt": f"{it[1]:,}".replace(",", ".")}
        if not ehPais:                 # língua e família têm índice próprio
            r["apelidos"] = sorted(set(it[2]))
        respostas.append(r)
    return {
        "tema": "linguas", "pergunta": pergunta, "escopo": escopo,
        "tipo_resposta": tipo,
        "fonte": fonte, "indicador": "", "ano": None, "unidade": unidade,
        "universo": universo,
        "disputada": abs(a - b) <= tol * max(a, b, 1e-9),
        "folga": round(abs(a - b) / max(a, b, 1e-9), 4),
        "nota": nota, "respostas": respostas,
    }


def cartas_de_linguas(paises, nomes, iso2_para_iso3, get_texto, sparql, norm,
                      problemas, min_paises_regiao=22):
    """Todas as cartas do tema línguas."""
    saida = []

    # ---------------------------------------------------- Glottolog
    try:
        bruto = get_texto(GLOTTOLOG_CSV, "glottolog_languages")
    except Exception as e:
        problemas.append(f"Glottolog indisponível ({e}) — cartas de língua puladas")
        bruto = None

    if bruto:
        linhas = list(csv.DictReader(io.StringIO(bruto)))
        nomes_glotto = {x["ID"]: x["Name"] for x in linhas}
        idiomas = [x for x in linhas if x["Level"] == "language"]

        # quantas línguas se fala em cada país
        por_pais, por_lingua = Counter(), Counter()
        for x in idiomas:
            paises_da_lingua = {iso2_para_iso3.get(c) for c in x["Countries"].split(";")}
            paises_da_lingua = {p for p in paises_da_lingua if p in paises}
            for iso3 in paises_da_lingua:
                por_pais[iso3] += 1
            if len(paises_da_lingua) > 1:
                por_lingua[x["ID"]] = len(paises_da_lingua)

        def itens_pais(filtro=None):
            it = [(nomes[i]["nome"], n, nomes[i]["apelidos"], i)
                  for i, n in por_pais.most_common()
                  if filtro is None or filtro(i)]
            return it

        it = itens_pais()
        saida.append(carta("Em quais países se fala o maior número de línguas?",
                           "Glottolog", "línguas faladas no território",
                           it, len(por_pais), "pais",
                           nota="Línguas vivas catalogadas pelo Glottolog, "
                                "não línguas oficiais."))
        for regiao, sufixo in (("África", "na África"), ("Ásia", "na Ásia"),
                               ("Américas", "nas Américas"), ("Europa", "na Europa")):
            it = itens_pais(lambda i, r=regiao: paises[i]["regiao"] == r)
            if len(it) >= min_paises_regiao:
                saida.append(carta(
                    f"Em quais países se fala o maior número de línguas {sufixo}?",
                    "Glottolog", "línguas faladas no território", it, len(it),
                    "pais", escopo=regiao,
                    nota="Línguas vivas catalogadas pelo Glottolog."))

        # famílias linguísticas
        fam = Counter()
        for x in idiomas:
            f = nomes_glotto.get(x["Family_ID"])
            if f and f not in PSEUDO_FAMILIAS:
                fam[f] += 1
            elif not x["Family_ID"] and x["Is_Isolate"] != "True":
                pass
        it = [(FAMILIAS_PT.get(f, f), n,
               {norm(FAMILIAS_PT.get(f, f)), norm(f)}, None)
              for f, n in fam.most_common()]
        saida.append(carta("Quais as famílias linguísticas com mais línguas?",
                           "Glottolog", "línguas na família", it, len(fam), "familia",
                           nota="Família é o grupo de línguas que descendem de um "
                                "ancestral comum. Conta língua viva catalogada pelo "
                                "Glottolog: dialeto não entra, e as gavetas internas "
                                "do catálogo (língua de sinais, não classificadas) "
                                "ficam de fora."))

    # ---------------------------------------------------- Wikidata: língua oficial
    q = """
    SELECT ?iso3 ?lang ?ptbr ?pt WHERE {
      ?p wdt:P298 ?iso3 ; wdt:P37 ?lang .
      OPTIONAL { ?lang rdfs:label ?ptbr . FILTER(LANG(?ptbr) = "pt-br") }
      OPTIONAL { ?lang rdfs:label ?pt   . FILTER(LANG(?pt)   = "pt") }
    }
    """
    try:
        d = sparql(q, "wd_lingua_oficial")
    except Exception as e:
        problemas.append(f"Wikidata P37 indisponível ({e})")
        return saida

    rotulo, onde = {}, defaultdict(set)
    for b in d["results"]["bindings"]:
        if b["iso3"]["value"] not in paises:      # fora território e país extinto
            continue
        q_id = b["lang"]["value"].rsplit("/", 1)[-1]
        n = (b.get("ptbr") or b.get("pt") or {}).get("value")
        if not n:
            continue
        # o Wikidata separa "inglês" de "inglês britânico"; na mesa é a mesma língua
        n = n.replace("língua ", "").replace("Língua ", "").strip()
        for variante in (" britânico", " americano", " europeu", " brasileiro"):
            if n.endswith(variante):
                n = n[: -len(variante)]
        rotulo[q_id] = n
        onde[n].add(b["iso3"]["value"])

    it = [(n, len(s), {norm(n)}, None)
          for n, s in sorted(onde.items(), key=lambda kv: -len(kv[1]))]
    c = carta("Quais as línguas oficiais em mais países?", "Wikidata",
              "países onde é oficial", it, len(onde), "lingua",
              nota="Só países soberanos. Fonte: propriedade P37 do Wikidata.")
    if c:
        saida.append(c)
    return saida
