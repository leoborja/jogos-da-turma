# -*- coding: utf-8 -*-
"""
Cartas do tema "Brasil": municípios e nomes de pessoa.

Fontes, as duas do IBGE e as duas abertas, sem chave:
  Censo 2022, tabela 4714   população, área e densidade dos 5.570 municípios
  Censo 2010, API de nomes  quantas pessoas se chamam cada nome, com recorte
                            por década de nascimento, por sexo e por estado

A API de nomes devolve tudo em caixa alta e sem acento (JOSE, ANTONIO). O
casamento do palpite já ignora acento, então isso só atrapalha na hora de ler
o gabarito — daí a tabela ACENTOS aqui embaixo, que é ortografia, não dado.
"""

from collections import defaultdict

SIDRA = ("https://apisidra.ibge.gov.br/values/t/4714/n6/all/v/93,6318,614/p/2022")
NOMES = "https://servicodados.ibge.gov.br/api/v2/censos/nomes/ranking"

REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Estados grandes o bastante pra render um top 10 que não seja a lista do país
# inteiro de novo. A dedup do gerador corta o que sobrar parecido demais.
UF_CODIGO = {"SP": 35, "MG": 31, "RJ": 33, "BA": 29, "RS": 43, "PR": 41,
             "PE": 26, "CE": 23, "PA": 15, "SC": 42, "GO": 52, "MA": 21}
# nome do estado já com a preposição certa: "no Rio de Janeiro", "na Bahia",
# "em Pernambuco". Sem isso o enunciado sai torto.
UF_NOME = {"SP": "São Paulo", "MG": "Minas Gerais", "RJ": "Rio de Janeiro",
           "BA": "Bahia", "RS": "Rio Grande do Sul", "PR": "Paraná",
           "PE": "Pernambuco", "CE": "Ceará", "PA": "Pará",
           "SC": "Santa Catarina", "GO": "Goiás", "MA": "Maranhão"}
UF_EM = {"SP": "em São Paulo", "MG": "em Minas Gerais", "RJ": "no Rio de Janeiro",
         "BA": "na Bahia", "RS": "no Rio Grande do Sul", "PR": "no Paraná",
         "PE": "em Pernambuco", "CE": "no Ceará", "PA": "no Pará",
         "SC": "em Santa Catarina", "GO": "em Goiás", "MA": "no Maranhão"}
UF_DE = {"SP": "de São Paulo", "MG": "de Minas Gerais", "RJ": "do Rio de Janeiro",
         "BA": "da Bahia", "RS": "do Rio Grande do Sul", "PR": "do Paraná",
         "PE": "de Pernambuco", "CE": "do Ceará", "PA": "do Pará",
         "SC": "de Santa Catarina", "GO": "de Goiás", "MA": "do Maranhão"}

CAPITAIS = {
    "Rio Branco", "Maceió", "Macapá", "Manaus", "Salvador", "Fortaleza",
    "Brasília", "Vitória", "Goiânia", "São Luís", "Cuiabá", "Campo Grande",
    "Belo Horizonte", "Belém", "João Pessoa", "Curitiba", "Recife", "Teresina",
    "Rio de Janeiro", "Natal", "Porto Alegre", "Porto Velho", "Boa Vista",
    "Florianópolis", "São Paulo", "Aracaju", "Palmas",
}

DECADAS = [1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]

# A API devolve sem acento. Isto aqui é grafia, não dado.
ACENTOS = {
    "JOSE": "José", "ANTONIO": "Antônio", "JOAO": "João", "SEBASTIAO": "Sebastião",
    "LUIS": "Luís", "MARCIA": "Márcia", "JESSICA": "Jéssica", "PATRICIA": "Patrícia",
    "FABIO": "Fábio", "TATIANE": "Tatiane", "VERONICA": "Verônica",
    "ROSANGELA": "Rosângela", "MARCIO": "Márcio", "VALERIA": "Valéria",
    "SILVIA": "Sílvia", "SONIA": "Sônia", "GERALDO": "Geraldo",
    "SIMONE": "Simone", "IZABEL": "Izabel", "ELIZABETE": "Elizabete",
    "VITORIA": "Vitória", "MONICA": "Mônica", "CICERO": "Cícero",
    "OTAVIO": "Otávio", "GLAUCIA": "Gláucia", "IRACEMA": "Iracema",
    "SEVERINO": "Severino", "GENIVALDO": "Genivaldo", "ELIANE": "Eliane",
    "ANDREA": "Andréa", "JULIO": "Júlio", "SERGIO": "Sérgio", "FLAVIA": "Flávia",
    "FLAVIO": "Flávio", "TARCISIO": "Tarcísio", "GERSON": "Gerson",
    "HELIO": "Hélio", "INACIO": "Inácio", "NILDA": "Nilda", "ADAO": "Adão",
    "SANDRA": "Sandra", "VERA": "Vera", "LUCIA": "Lúcia", "LUCIANA": "Luciana",
}


def bonito(nome):
    """MARIA -> Maria, JOSE -> José."""
    return ACENTOS.get(nome, nome.title())


def num(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def carrega_municipios(get_json, problemas):
    """
    (nome, uf) -> {pop, area, densidade}. Nome que se repete em mais de um
    estado (tem 5 "Bom Jesus") ganha a UF colada, senão o gabarito mente.
    """
    try:
        d = get_json(SIDRA, "ibge_municipios")
    except Exception as e:
        problemas.append(f"IBGE tabela 4714 indisponível ({e}) — cartas de município puladas")
        return {}

    bruto = defaultdict(dict)
    for r in d[1:]:
        rotulo = r.get("D1N", "")
        if " - " not in rotulo:
            continue
        nome, uf = rotulo.rsplit(" - ", 1)
        bruto[(nome, uf)][r.get("D2N", "")] = r.get("V")

    quantos = defaultdict(int)
    for nome, _ in bruto:
        quantos[nome] += 1

    saida = {}
    for (nome, uf), v in bruto.items():
        pop = num(v.get("População residente"))
        if not pop:
            continue
        saida[(nome, uf)] = {
            "nome": nome if quantos[nome] == 1 else f"{nome} ({uf})",
            "uf": uf,
            "regiao": REGIAO.get(uf),
            "pop": pop,
            "area": num(v.get("Área da unidade territorial")),
            "densidade": num(v.get("Densidade demográfica")),
            "unico": quantos[nome] == 1,
        }
    return saida


def carrega_nomes(get_json, problemas):
    """Todos os recortes do ranking de nomes que a gente usa."""
    pedidos = {"brasil": {}, "homem": {"sexo": "M"}, "mulher": {"sexo": "F"}}
    for d in DECADAS:
        pedidos[f"dec{d}"] = {"decada": d}
    for uf, cod in UF_CODIGO.items():
        pedidos[f"uf{uf}"] = {"localidade": cod}

    saida = {}
    for chave, params in pedidos.items():
        url = NOMES + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else "")
        try:
            d = get_json(url, f"ibge_nomes_{chave}")
            saida[chave] = [(x["nome"], x["frequencia"]) for x in d[0]["res"]]
        except Exception as e:
            problemas.append(f"IBGE nomes ({chave}) falhou: {e}")
    return saida


# ---------------------------------------------------------------- as cartas

def carta(pergunta, fonte, unidade, itens, universo, tipo, escopo, nota,
          ano=None, tol=0.005, fmt=None):
    """itens = [(chave, nome, valor), ...] já ordenado. None se não der top 10."""
    if len(itens) < 11:
        return None
    dez, onze = itens[:10], itens[10]
    a, b = abs(dez[-1][2]), abs(onze[2])
    def escreve(v):
        s = f"{v:,.0f}" if fmt != "km2" else f"{v:,.0f} km²"
        return s.replace(",", ".")
    return {
        "tema": "brasil", "pergunta": pergunta, "escopo": "Brasil",
        "fonte": fonte, "indicador": "", "ano": ano, "unidade": unidade,
        "universo": universo, "tipo_resposta": tipo, "nota": nota,
        "disputada": abs(a - b) <= tol * max(a, b, 1e-9),
        "folga": round(abs(a - b) / max(a, b, 1e-9), 4),
        "respostas": [{"pos": i + 1, "chave": c, "nome": n, "valor": v,
                       "valor_fmt": escreve(v)}
                      for i, (c, n, v) in enumerate(dez)],
    }


def cartas_do_brasil(get_json, norm, problemas):
    """Devolve (cartas, indice_municipios, indice_nomes)."""
    cartas = []
    mun = carrega_municipios(get_json, problemas)

    def top(campo, filtro=None, maior=True):
        it = [(f"{n}|{u}", d["nome"], d[campo]) for (n, u), d in mun.items()
              if d.get(campo) and (filtro is None or filtro(d))]
        it.sort(key=lambda x: -x[2] if maior else x[2])
        return it

    if mun:
        NOTA_POP = ("População residente contada pelo Censo de 2022. É o "
                    "município inteiro, não só a área urbana.")
        it = top("pop")
        cartas.append(carta("Quais os municípios mais populosos do Brasil?",
                            "IBGE, Censo 2022", "habitantes", it, len(it),
                            "municipio", "Brasil", NOTA_POP, 2022))
        for regiao in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"):
            it = top("pop", lambda d, r=regiao: d["regiao"] == r)
            c = carta(f"Quais os municípios mais populosos do {regiao}?"
                      if regiao != "Norte" else
                      "Quais os municípios mais populosos do Norte?",
                      "IBGE, Censo 2022", "habitantes", it, len(it),
                      "municipio", regiao, NOTA_POP, 2022)
            if c:
                cartas.append(c)
        for uf, nome_uf in UF_NOME.items():
            it = top("pop", lambda d, u=uf: d["uf"] == u)
            c = carta(f"Quais os municípios mais populosos {UF_DE[uf]}?",
                      "IBGE, Censo 2022", "habitantes", it, len(it),
                      "municipio", nome_uf, NOTA_POP, 2022)
            if c:
                cartas.append(c)

        it = top("area")
        cartas.append(carta("Quais os maiores municípios do Brasil em área?",
                            "IBGE, Censo 2022", "km²", it, len(it), "municipio",
                            "Brasil",
                            "Área do território do município. Os gigantes ficam "
                            "todos na Amazônia, onde um município sozinho é "
                            "maior que muito país europeu.", 2022, fmt="km2"))
        it = top("densidade")
        cartas.append(carta("Quais os municípios mais densamente povoados do Brasil?",
                            "IBGE, Censo 2022", "hab/km²", it, len(it),
                            "municipio", "Brasil",
                            "População dividida pela área do município. Quem "
                            "ganha não é a capital grande, é a cidade pequena e "
                            "espremida da região metropolitana.", 2022))
        it = top("pop", lambda d: d["nome"] in CAPITAIS)
        cartas.append(carta("Quais as capitais mais populosas do Brasil?",
                            "IBGE, Censo 2022", "habitantes", it, 27,
                            "municipio", "Brasil",
                            "Só as 27 capitais, incluindo Brasília. É a "
                            "população do município, não da região "
                            "metropolitana — senão Belo Horizonte passaria "
                            "Fortaleza.", 2022))

    # ---------------------------------------------------------------- nomes
    nomes = carrega_nomes(get_json, problemas)
    NOTA_NOME = ("Quantas pessoas vivas em 2010 tinham esse nome de registro, "
                 "pelo Censo. Conta só o primeiro nome.")

    def cartaz(chave, pergunta, escopo, nota=NOTA_NOME):
        lista = nomes.get(chave) or []
        it = [(norm(n), bonito(n), f) for n, f in lista]
        return carta(pergunta, "IBGE, Censo 2010", "pessoas com esse nome",
                     it, len(it), "nome", escopo, nota, 2010)

    for chave, pergunta, escopo in (
        ("brasil", "Quais os nomes mais comuns do Brasil?", "Brasil"),
        ("mulher", "Quais os nomes de mulher mais comuns do Brasil?", "Brasil"),
        ("homem", "Quais os nomes de homem mais comuns do Brasil?", "Brasil"),
    ):
        c = cartaz(chave, pergunta, escopo)
        if c:
            cartas.append(c)

    for d in DECADAS:
        c = cartaz(f"dec{d}",
                   f"Quais os nomes que mais se deu a quem nasceu nos anos {d}?",
                   f"anos {d}",
                   "Quantas pessoas nascidas nessa década tinham esse nome no "
                   "Censo de 2010. Quem morreu antes de 2010 não está aqui, "
                   "então as décadas antigas vêm um pouco encolhidas.")
        if c:
            cartas.append(c)

    for uf, nome_uf in UF_NOME.items():
        c = cartaz(f"uf{uf}", f"Quais os nomes mais comuns {UF_EM[uf]}?", nome_uf)
        if c:
            cartas.append(c)

    indice_mun = {f"{n}|{u}": {"nome": d["nome"],
                               "apelidos": sorted({norm(d["nome"]), norm(n),
                                                   norm(f"{n} {u}")})}
                  for (n, u), d in mun.items()}
    vistos = set()
    indice_nome = {}
    for lista in nomes.values():
        for n, _ in lista:
            if norm(n) not in vistos:
                vistos.add(norm(n))
                indice_nome[norm(n)] = {"nome": bonito(n), "apelidos": [norm(n)]}
    return cartas, indice_mun, indice_nome
