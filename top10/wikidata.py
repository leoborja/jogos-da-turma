# -*- coding: utf-8 -*-
"""
Pedaços de SPARQL que os temas do Wikidata dividem.

O problema recorrente: nem todo item tem rótulo em português. O Forrest Gump,
por exemplo, só tem rótulo em chinês — mas tem artigo na Wikipédia lusófona.
Por isso o nome é montado em cascata: pt-br, pt, título do artigo em português,
en, título do artigo em inglês. Sem isso, um filme conhecidíssimo sumiria do
top 10 e a carta ficaria errada em silêncio.
"""

# ?x é o item; devolve ?nome já resolvido e ?apelidos (altLabel em pt)
NOME = """
  OPTIONAL {{ ?{v} rdfs:label ?{v}_ptbr FILTER(LANG(?{v}_ptbr) = "pt-br") }}
  OPTIONAL {{ ?{v} rdfs:label ?{v}_pt   FILTER(LANG(?{v}_pt)   = "pt")    }}
  OPTIONAL {{ ?{v} rdfs:label ?{v}_en   FILTER(LANG(?{v}_en)   = "en")    }}
  OPTIONAL {{ ?{v}_a  schema:about ?{v} ; schema:isPartOf <https://pt.wikipedia.org/> ;
              schema:name ?{v}_wpt }}
  OPTIONAL {{ ?{v}_a2 schema:about ?{v} ; schema:isPartOf <https://en.wikipedia.org/> ;
              schema:name ?{v}_wen }}
  BIND(COALESCE(?{v}_ptbr, ?{v}_pt, ?{v}_wpt, ?{v}_en, ?{v}_wen) AS ?{v}_nome)
"""


def nome_de(var):
    return NOME.format(v=var)


def item(binding, var, norm):
    """
    Lê um item de um resultado SPARQL. Devolve (chave, nome, apelidos) ou None
    quando não deu pra nomear — carta com resposta sem nome não vai pro baralho.
    """
    nome = binding.get(f"{var}_nome", {}).get("value")
    if not nome:
        return None
    chave = binding[var]["value"].rsplit("/", 1)[-1]      # o Q-id
    apelidos = {norm(nome)}
    cru = binding.get(f"{var}_apelidos", {}).get("value", "")
    for a in cru.split("|"):
        a = norm(a)
        if len(a) > 2:
            apelidos.add(a)
    return chave, nome, sorted(apelidos)


def carta(pergunta, fonte, unidade, itens, universo, tipo, escopo, nota,
          formata, tema, ano=None, tol=0.0):
    """
    tol baixo de propósito. A régua de 0,5% do tema países existe porque
    indicador do Banco Mundial é estimativa e meio ponto percentual é ruído.
    Bilheteria, capacidade de estádio e contagem de título são número exato,
    não estimativa. Aqui empate é só empate de verdade (tol=0): 0,25% de
    diferença em bilheteria é diferença real, e descartar por isso jogaria
    fora justamente as cartas boas.
    """
    """itens = [(chave, nome, apelidos, valor), ...] já ordenado."""
    if len(itens) < 11:
        return None
    dez, onze = itens[:10], itens[10]
    a, b = abs(dez[-1][3]), abs(onze[3])
    return {
        "tema": tema, "pergunta": pergunta, "escopo": escopo,
        "fonte": fonte, "indicador": "", "ano": ano, "unidade": unidade,
        "universo": universo, "tipo_resposta": tipo, "nota": nota,
        "disputada": abs(a - b) <= tol * max(a, b, 1e-9),
        "folga": round(abs(a - b) / max(a, b, 1e-9), 4),
        "respostas": [{"pos": i + 1, "chave": c, "nome": n, "valor": v,
                       "valor_fmt": formata(v)}
                      for i, (c, n, _, v) in enumerate(dez)],
    }


def indexa(por_tipo):
    """
    {tipo: [lista de itens]} -> {tipo: {chave: {nome, apelidos}}}.
    Cada tipo tem o índice DELE: carta de filme não pode sugerir diretor.
    """
    idx = {}
    for tipo, listas in por_tipo.items():
        alvo = idx.setdefault(tipo, {})
        for lista in listas:
            for chave, nome, apelidos, _ in lista:
                alvo.setdefault(chave, {"nome": nome, "apelidos": apelidos})
    return idx
