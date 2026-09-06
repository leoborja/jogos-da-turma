#!/usr/bin/env python3
"""
gerador.py — monta o baralho do Imagem e Ação a partir de bases abertas.

A carta do jogo de caixa traz uma palavra e uma letra dizendo em que casa ela
joga: O de objeto, P de pessoa/lugar/animal, A de ação, D de difícil. A letra é
o que a mesa mais discute ("isso não é objeto!"), então aqui ela não é palpite:

  a casa       é o arquivo lexicográfico da WordNet de Princeton. Cada sentido
               mora em exatamente um dos 45 arquivos temáticos — noun.animal,
               noun.artifact, verb.motion — e casas.py diz qual arquivo cai em
               qual casa. Quando a palavra tem sentido em mais de uma casa,
               fica com a mais concreta: é a que dá desenho.

  a palavra    é um lema em português da OpenWordnet-PT, confirmado como
               substantivo ou verbo pelo Wikcionário e presente na lista de
               frequência do português falado — palavra que ninguém usa não
               vira desenho.

  a cadeia     que a carta mostra ("martelo → ferramenta → apetrecho →
               artefato") são os hiperônimos da OpenWordnet-PT. É o que prova
               a casa e, de quebra, é a primeira ideia de desenho.

  a raridade   é a posição da palavra na lista de frequência.

Uso:
    python3 gerador.py                  # gera o baralho
    python3 gerador.py --por-casa 200   # muda o teto de cartas por casa
    python3 gerador.py --topo 25000     # aceita palavra mais rara
    python3 gerador.py --sem-cache      # rebaixa tudo

Saídas:
    banco.json     -> o baralho pronto pro jogo
    revisao.csv    -> uma linha por carta, pra conferir com o olho
    relatorio.txt  -> o que entrou, o que caiu e por quê
    cache/         -> as bases cruas (re-rodar fica instantâneo)
"""

import argparse, collections, csv, datetime, hashlib, json, os, re, sys, tarfile
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET

from casas import (CASAS, CASA_DO_ARQUIVO, ARQUIVOS, PRIORIDADE,
                   IMPROPRIAS, VETADAS)

UA = "JogosDaTurma/0.1 (https://github.com/leoborja/jogos-da-turma; leo@cloudarbitration.com)"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
WIKT = "https://pt.wiktionary.org/w/api.php"

OWNPT_URL = ("https://github.com/own-pt/openWordnet-PT/releases/download/v1.1.0/"
             "own-pt-2026.04.07.tar.xz")
WN30_URL = "https://wordnetcode.princeton.edu/3.0/WNdb-3.0.tar.gz"
FREQ_URL = ("https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/"
            "content/2018/pt_br/pt_br_50k.txt")

# Os 45 arquivos lexicográficos da WordNet 3.0, na ordem do lex_filenum que
# aparece no segundo campo de data.noun e data.verb.
# https://wordnet.princeton.edu/documentation/lexnames5wn
LEXNAMES = """adj.all adj.pert adv.all noun.Tops noun.act noun.animal noun.artifact
noun.attribute noun.body noun.cognition noun.communication noun.event noun.feeling
noun.food noun.group noun.location noun.motive noun.object noun.person noun.phenomenon
noun.plant noun.possession noun.process noun.quantity noun.relation noun.shape noun.state
noun.substance noun.time verb.body verb.change verb.cognition verb.communication
verb.competition verb.consumption verb.contact verb.creation verb.emotion verb.motion
verb.perception verb.possession verb.social verb.stative verb.weather adj.ppl""".split()

# A raridade é a posição na lista de frequência do português falado.
FAIXAS = [(2000, "comum"), (7000, "conhecida"), (10**9, "rara")]

SEM_CACHE = False


# ------------------------------------------------------------------ utilidades

def baixa(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(r, timeout=120).read()


def arquivo_baixado(nome, url):
    """baixa uma vez pro cache e devolve o caminho."""
    os.makedirs(CACHE, exist_ok=True)
    destino = os.path.join(CACHE, nome)
    if not os.path.exists(destino):
        print(f"· baixando {nome}…")
        with open(destino, "wb") as fh:
            fh.write(baixa(url))
    return destino


def cache_json(chave, produz):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, hashlib.md5(chave.encode()).hexdigest() + ".json")
    if os.path.exists(f) and not SEM_CACHE:
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    v = produz()
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(v, fh, ensure_ascii=False)
    return v


def api(base, **kw):
    kw.setdefault("format", "json")
    kw.setdefault("formatversion", "2")
    url = base + "?" + urllib.parse.urlencode(kw)
    return cache_json(url, lambda: json.loads(baixa(url)))


def descompacta(caminho, marca):
    """abre o .tar dentro do cache uma vez só; marca é um arquivo que sobra."""
    alvo = os.path.join(CACHE, marca)
    if not os.path.exists(alvo):
        print(f"· abrindo {os.path.basename(caminho)}…")
        with tarfile.open(caminho) as t:
            t.extractall(CACHE)
    return alvo


# ------------------------------------------------------------------- as bases

def wordnet_princeton():
    """{(offset, pos): (arquivo lexicográfico, quantas vezes o sentido foi visto)}.

    O arquivo lexicográfico é o segundo campo de data.noun/data.verb. A contagem
    vem do quarto campo de index.sense — é quantas vezes aquele sentido apareceu
    no corpus etiquetado de Princeton, e é o que diz qual é o sentido de sempre
    quando a palavra tem vários.
    """
    dic = descompacta(arquivo_baixado("WNdb-3.0.tar.gz", WN30_URL), "dict")
    arquivo, visto = {}, collections.defaultdict(int)
    for nome, pos in (("data.noun", "n"), ("data.verb", "v")):
        with open(os.path.join(dic, nome), encoding="latin-1") as fh:
            for linha in fh:
                if linha.startswith("  "):
                    continue
                p = linha.split()
                arquivo[(p[0], pos)] = LEXNAMES[int(p[1])]
    with open(os.path.join(dic, "index.sense"), encoding="latin-1") as fh:
        for linha in fh:
            p = linha.split()
            pos = {"1": "n", "2": "v"}.get(p[0].split("%")[1][0])
            if pos:
                visto[(p[1], pos)] = max(visto[(p[1], pos)], int(p[3]))
    return arquivo, visto


def wordnet_portugues():
    """lê a OpenWordnet-PT: lemas, hiperônimos e definições em português."""
    pasta = descompacta(arquivo_baixado("own-pt.tar.xz", OWNPT_URL), "own-pt")
    xml = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".xml")][0]
    lexicon = ET.parse(xml).getroot()[0]

    acima = collections.defaultdict(list)     # synset -> hiperônimos
    definicao = {}                            # synset -> definição em português
    for s in lexicon.iter("Synset"):
        sid = s.get("id")
        for r in s.findall("SynsetRelation"):
            if r.get("relType") in ("hypernym", "instance_hypernym"):
                acima[sid].append(r.get("target"))
        d = s.find("Definition")
        if d is not None and d.text:
            definicao[sid] = d.text.strip()

    sentidos = collections.defaultdict(list)  # (palavra, pos) -> [synsets]
    nomes = collections.defaultdict(list)     # synset -> [palavras em pt]
    for e in lexicon.iter("LexicalEntry"):
        lema = e.find("Lemma")
        palavra, pos = lema.get("writtenForm"), lema.get("partOfSpeech")
        for sense in e.findall("Sense"):
            sid = sense.get("synset")
            sentidos[(palavra, pos)].append(sid)
            nomes[sid].append(palavra)
    return sentidos, nomes, acima, definicao


def lista_frequencia():
    """{palavra: posição} no português falado, do mais comum pro menos."""
    caminho = arquivo_baixado("pt_br_50k.txt", FREQ_URL)
    freq = {}
    with open(caminho, encoding="utf-8") as fh:
        for i, linha in enumerate(fh):
            p = linha.split()
            if len(p) == 2 and p[0] not in freq:
                freq[p[0]] = i + 1
    return freq


def categoria_wikcionario(nome):
    """todos os verbetes de uma categoria gramatical do Wikcionário."""
    saida, cont = [], None
    while True:
        kw = dict(action="query", list="categorymembers", cmtitle=nome,
                  cmlimit="500", cmnamespace="0")
        if cont:
            kw["cmcontinue"] = cont
        d = api(WIKT, **kw)
        saida += [m["title"] for m in d["query"]["categorymembers"]]
        cont = d.get("continue", {}).get("cmcontinue")
        if not cont:
            return saida


# Substantivo e verbo dizem quem entra. O resto da lista diz quem sai: se a
# palavra também é advérbio, numeral ou forma flexionada, a posição dela na
# lista de frequência é do outro sentido, não do substantivo — "bem", "boa" e
# "dois" são palavras comuníssimas cujo substantivo ninguém usa.
#
# Adjetivo fica de fora dessa peneira de propósito: em português quase todo
# substantivo de gente e de bicho também é adjetivo ("gato", "cachorro",
# "médico", "soldado"), e barrar por isso levaria meio baralho junto. Os
# particípios que sobram ("morto", "dado", "conhecido") caem na mão, em
# casas.py.
CLASSES = ["Substantivo", "Verbo", "Adjetivo", "Advérbio", "Numeral", "Pronome",
           "Preposição", "Conjunção", "Artigo", "Interjeição",
           "Forma de substantivo", "Forma de adjetivo"]
SO_SUBSTANTIVO = ["Advérbio", "Numeral", "Pronome", "Preposição", "Conjunção",
                  "Artigo", "Interjeição", "Forma de substantivo", "Forma de adjetivo"]


def dicionario():
    """{classe: conjunto de verbetes} — quem diz que a palavra existe em pt.

    A OpenWordnet-PT nasceu de tradução automática e às vezes pendura num
    synset de substantivo uma palavra que em português é verbo ou advérbio
    ("adiar" como noun.act, "agora" como noun.time). O Wikcionário desempata.
    """
    print("· lendo as classes gramaticais do Wikcionário…")
    d = {}
    for classe in CLASSES:
        d[classe] = {w.lower() for w in
                     categoria_wikcionario(f"Categoria:{classe} (Português)")}
        print(f"    {classe}: {len(d[classe])}")
    return d


LIMPA = [
    (re.compile(r"\[\[[^\]|]*\|([^\]]*)\]\]"), r"\1"),   # [[alvo|texto]] -> texto
    (re.compile(r"\[\[([^\]]*)\]\]"), r"\1"),            # [[texto]]      -> texto
    (re.compile(r"\{\{[^}]*\}\}"), ""),                   # {{modelo}}     -> nada
    (re.compile(r"<[^>]+>"), ""),
    (re.compile(r"'{2,}"), ""),
    (re.compile(r"\s+"), " "),
]
SECAO_PT = re.compile(r"=\s*\{\{-pt-\}\}\s*=")
OUTRA_LINGUA = re.compile(r"^=\s*\{\{-(?!pt-)[a-z-]+\}\}\s*=", re.M)
CABECALHO = re.compile(r"^=+\s*(Substantivo|Verbo)[^=]*=+\s*$", re.M | re.I)


def definicao_wikcionario(palavras, classe_de):
    """{palavra: primeira definição em português} lida do texto do verbete.

    O verbete do Wikcionário é uma pilha de línguas; interessa o pedaço do
    português, dentro dele o cabeçalho da classe da carta, e dentro dele a
    primeira linha que começa com "#". É o mesmo texto que o jogador vê ao
    abrir o link da carta.
    """
    saida = {}
    palavras = sorted(set(palavras))
    for i in range(0, len(palavras), 50):
        lote = palavras[i:i + 50]
        d = api(WIKT, action="query", prop="revisions", rvprop="content",
                rvslots="main", titles="|".join(lote))
        for pag in d.get("query", {}).get("pages", []):
            try:
                texto = pag["revisions"][0]["slots"]["main"]["content"]
            except (KeyError, IndexError):
                continue
            m = SECAO_PT.search(texto)
            if not m:
                continue
            pedaco = texto[m.end():]
            fim = OUTRA_LINGUA.search(pedaco)
            if fim:
                pedaco = pedaco[:fim.start()]
            alvo = "Substantivo" if classe_de.get(pag["title"].lower()) == "n" else "Verbo"
            cabecalhos = [c for c in CABECALHO.finditer(pedaco)
                          if c.group(1).lower() == alvo.lower()]
            if not cabecalhos:
                continue
            corpo = pedaco[cabecalhos[0].end():]
            proximo = CABECALHO.search(corpo)
            if proximo:
                corpo = corpo[:proximo.start()]
            for linha in corpo.splitlines():
                linha = linha.strip()
                if not linha.startswith("#") or linha.startswith(("#:", "#*", "##")):
                    continue
                frase = linha.lstrip("# ").strip()
                for regex, troca in LIMPA:
                    frase = regex.sub(troca, frase)
                frase = frase.strip(" .;:,")
                if 3 <= len(frase) <= 130:
                    saida[pag["title"].lower()] = frase[0].lower() + frase[1:]
                break
        print(f"\r    definições {min(i + 50, len(palavras))}/{len(palavras)}",
              end="", flush=True)
    print()
    return saida


# ---------------------------------------------------------------- a montagem

def faixa(posicao):
    for teto, nome in FAIXAS:
        if posicao <= teto:
            return nome


def cadeia_ate(palavra, sid, acima, nomes, passos=4):
    """['martelo', 'ferramenta', 'apetrecho', 'artefato'] — o caminho pra cima.

    Começa na palavra da carta (o synset tem vários nomes, e o primeiro nem
    sempre é o dela). A OpenWordnet-PT tem synset sem nome em português e
    synset cujo nome repete o do filho; os dois são pulados, senão a cadeia
    vira "ferramenta → ferramenta → ferramenta".
    """
    saida, atual, visto = [palavra.lower()], sid, {sid}
    while atual and len(saida) < passos:
        proximos = [p for p in acima.get(atual, []) if p not in visto]
        if not proximos:
            break
        atual = proximos[0]
        visto.add(atual)
        nome = nomes.get(atual, [None])[0]
        if nome and nome.lower() != saida[-1].lower():
            saida.append(nome)
    return saida


def quanto_visto(palavra, sentidos, arquivo, visto):
    """soma das contagens de todos os sentidos da palavra, substantivo e verbo."""
    total = 0
    for p in ("n", "v"):
        for sid in sentidos.get((palavra, p), []):
            total += visto[(sid.rsplit("-", 2)[-2], p)]
    return total


def escolhe_sentido(palavra, pos, sentidos, arquivo, visto):
    """entre os sentidos da palavra, o que vira carta.

    Vale o sentido mais visto no corpus de Princeton; empatou, ganha a casa mais
    concreta. Sentido que cai fora das quatro casas não conta.
    """
    candidatos = []
    for sid in sentidos.get((palavra, pos), []):
        offset = sid.rsplit("-", 2)[-2]
        arq = arquivo.get((offset, pos))
        casa = CASA_DO_ARQUIVO.get(arq)
        if casa:
            candidatos.append((-visto[(offset, pos)], PRIORIDADE[casa], offset, sid, arq, casa))
    if not candidatos:
        return None
    candidatos.sort()
    _, _, _, sid, arq, casa = candidatos[0]
    return sid, arq, casa


def monta(args):
    arquivo, visto = wordnet_princeton()
    sentidos, nomes, acima, definicao = wordnet_portugues()
    freq = lista_frequencia()
    dic = dicionario()

    caiu = collections.Counter()
    cartas = []
    for (palavra, pos), _ in sentidos.items():
        if pos not in ("n", "v"):
            continue
        p = palavra.lower()
        if palavra != p or not palavra.isalpha() or len(palavra) < 3:
            caiu["não é uma palavra só, minúscula e sem número"] += 1
            continue
        if p in IMPROPRIAS or p in VETADAS:
            caiu["está na lista de fora"] += 1
            continue
        posicao = freq.get(p)
        if posicao is None or posicao > args.topo:
            caiu["fora da lista de frequência"] += 1
            continue
        if pos == "n":
            if p not in dic["Substantivo"]:
                caiu["o Wikcionário não diz que é substantivo"] += 1
                continue
            if any(p in dic[c] for c in SO_SUBSTANTIVO):
                caiu["é substantivo, mas é mais usada como outra classe"] += 1
                continue
        else:
            if p not in dic["Verbo"]:
                caiu["o Wikcionário não diz que é verbo"] += 1
                continue
            if not p.endswith(("ar", "er", "ir", "or")):
                caiu["verbo que não está no infinitivo"] += 1
                continue
        escolha = escolhe_sentido(palavra, pos, sentidos, arquivo, visto)
        if not escolha:
            caiu["nenhum sentido cai numa das quatro casas"] += 1
            continue
        sid, arq, casa = escolha
        # O sentido que virou carta precisa ser O sentido da palavra. Se nunca
        # foi visto no corpus de Princeton, ou se responde por menos da metade
        # das aparições da palavra, quem ler a carta vai pensar em outra coisa.
        vezes = visto[(sid.rsplit("-", 2)[-2], pos)]
        todas = quanto_visto(p, sentidos, arquivo, visto)
        if vezes < 2:
            caiu["sentido que quase não aparece"] += 1
            continue
        if todas and vezes / todas < 0.5:
            caiu["a palavra é mais usada em outro sentido"] += 1
            continue
        # A cadeia é o enfeite que prova a casa; nem todo synset tem nome em
        # português acima dele, e "cabeça" sem cadeia continua sendo uma ótima
        # carta. Quando falta cadeia, quem explica a casa é o arquivo.
        cadeia = cadeia_ate(palavra, sid, acima, nomes)
        cartas.append({
            "palavra": palavra.upper(),
            "casa": casa,
            "sentido": definicao.get(sid, ""),
            "sentido_de": "OpenWordnet-PT" if definicao.get(sid) else "",
            "pos": pos,
            "cadeia": cadeia,
            "arquivo": arq,
            "raridade": faixa(posicao),
            "posicao": posicao,
            "synset": sid.replace("own-pt-synset-", ""),
            "url": "https://pt.wiktionary.org/wiki/" + urllib.parse.quote(p),
        })

    # Onde a OpenWordnet-PT não escreveu definição em português, quem explica a
    # palavra é o Wikcionário — que é justamente o link que a carta abre.
    faltando = [c for c in cartas if not c["sentido"]]
    if faltando:
        print(f"· buscando no Wikcionário o sentido de {len(faltando)} palavras…")
        classe_de = {c["palavra"].lower(): c["pos"] for c in faltando}
        achadas = definicao_wikcionario([c["palavra"].lower() for c in faltando], classe_de)
        for c in faltando:
            texto = achadas.get(c["palavra"].lower())
            if texto:
                c["sentido"], c["sentido_de"] = texto, "Wikcionário"

    # Teto por casa: as mais comuns primeiro. Palavra rara não vira desenho, e
    # sem teto a casa Objeto sozinha seria metade do baralho.
    cartas.sort(key=lambda c: c["posicao"])
    por_casa, escolhidas = collections.Counter(), []
    for c in cartas:
        if por_casa[c["casa"]] >= args.por_casa:
            caiu["passou do teto da casa"] += 1
            continue
        por_casa[c["casa"]] += 1
        escolhidas.append(c)
    escolhidas.sort(key=lambda c: (c["casa"], c["palavra"]))
    return escolhidas, caiu, por_casa


def escreve(cartas, caiu, por_casa, args):
    aqui = os.path.dirname(os.path.abspath(__file__))
    banco = {
        "gerado_em": datetime.date.today().isoformat(),
        "fontes": [
            {"nome": "OpenWordnet-PT",
             "papel": "as palavras em português, os hiperônimos da cadeia e as definições",
             "url": "https://github.com/own-pt/openWordnet-PT",
             "licenca": "CC BY 4.0"},
            {"nome": "WordNet 3.0 (Princeton)",
             "papel": "o arquivo lexicográfico que decide a casa da carta",
             "url": "https://wordnet.princeton.edu/",
             "licenca": "licença WordNet 3.0"},
            {"nome": "Wikcionário em português",
             "papel": "confirma que a palavra é mesmo substantivo ou verbo, e é o link de conferir",
             "url": "https://pt.wiktionary.org",
             "licenca": "CC BY-SA 4.0"},
            {"nome": "FrequencyWords (OpenSubtitles 2018, pt-BR)",
             "papel": "diz se a palavra é conhecida e mede a raridade",
             "url": "https://github.com/hermitdave/FrequencyWords",
             "licenca": "CC BY-SA 4.0"},
        ],
        "metodo": (
            "A casa de cada carta é o arquivo lexicográfico em que a WordNet de "
            "Princeton guarda aquele sentido: noun.artifact vira Objeto, noun.animal "
            "vira Pessoa/lugar/bicho, verb.motion vira Ação, noun.feeling vira "
            "Difícil. Quando a palavra tem sentido em mais de uma casa, vale o "
            "sentido mais visto no corpus etiquetado de Princeton e, no empate, a "
            "casa mais concreta — é a que dá desenho. A cadeia que a carta mostra "
            "são os hiperônimos da OpenWordnet-PT, e é ela que prova a casa. Só "
            "entra palavra que o Wikcionário confirma e que aparece na lista de "
            "frequência do português falado."),
        "casas": [{k: c[k] for k in ("id", "nome", "letra", "cor", "o_que_e")} for c in CASAS],
        "arquivos": ARQUIVOS,
        "cartas": [{k: v for k, v in c.items() if k != "pos"} for c in cartas],
    }
    with open(os.path.join(aqui, "banco.json"), "w", encoding="utf-8") as fh:
        json.dump(banco, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    with open(os.path.join(aqui, "revisao.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["palavra", "casa", "arquivo", "raridade", "posicao", "cadeia",
                    "sentido", "sentido_de"])
        for c in cartas:
            w.writerow([c["palavra"], c["casa"], c["arquivo"], c["raridade"],
                        c["posicao"], " > ".join(c["cadeia"]), c["sentido"],
                        c["sentido_de"]])

    linhas = [f"baralho gerado em {banco['gerado_em']}",
              f"teto por casa: {args.por_casa} · topo da frequência: {args.topo}", "",
              f"{len(cartas)} cartas:"]
    for c in CASAS:
        linhas.append(f"  {c['letra']}  {c['nome']:<26} {por_casa[c['id']]:>4}")
    linhas += ["", "por raridade:"]
    for nome, n in collections.Counter(c["raridade"] for c in cartas).most_common():
        linhas.append(f"  {nome:<12} {n:>4}")
    linhas += ["", "candidatas que caíram:"]
    for motivo, n in caiu.most_common():
        linhas.append(f"  {n:>6}  {motivo}")
    linhas += ["", "as 25 primeiras de cada casa (as mais comuns):"]
    for c in CASAS:
        do = [x for x in sorted(cartas, key=lambda c: c["posicao"]) if x["casa"] == c["id"]]
        linhas.append(f"  {c['nome']}: " + ", ".join(x["palavra"].lower() for x in do[:25]))
    texto = "\n".join(linhas) + "\n"
    with open(os.path.join(aqui, "relatorio.txt"), "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(texto)


def main():
    global SEM_CACHE
    ap = argparse.ArgumentParser(description="monta o baralho do Imagem e Ação")
    ap.add_argument("--por-casa", type=int, default=180, help="teto de cartas por casa")
    ap.add_argument("--topo", type=int, default=15000,
                    help="até que posição da lista de frequência a palavra vale")
    ap.add_argument("--sem-cache", action="store_true", help="ignora o cache das APIs")
    args = ap.parse_args()
    SEM_CACHE = args.sem_cache
    cartas, caiu, por_casa = monta(args)
    escreve(cartas, caiu, por_casa, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
