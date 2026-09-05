#!/usr/bin/env python3
"""
gerador.py — monta o baralho do Tabu a partir de bases abertas.

A pergunta que a carta responde é: "quais são as cinco palavras que qualquer
pessoa usaria pra explicar ISTO?". A resposta não é opinião — é medida:

  palavra-chave  vem de uma lista de frequência do português falado
                 (OpenSubtitles / hermitdave FrequencyWords, CC BY-SA 4.0),
                 filtrada pelos substantivos do Wikcionário em português.

  proibidas      são os substantivos mais característicos do artigo da
                 Wikipédia em português sobre a palavra: TF-IDF do texto do
                 artigo contra (a) o resto do baralho e (b) o português falado.
                 Palavra que aparece em todo artigo não é característica.

  dificuldade    é a posição da palavra-chave na lista de frequência.

O teto de --cartas é por faixa, não total: nunca se raspa mais de 70% de uma
faixa, porque só existem tantas palavras muito comuns e o fundo da faixa
"fácil" é onde mora a carta ruim.

Uso:
    python3 gerador.py                # gera o baralho (221 cartas hoje)
    python3 gerador.py --cartas 400   # sobe o teto por faixa
    python3 gerador.py --sem-cache    # ignora cache/ e rebaixa tudo

Saídas:
    banco.json      -> o baralho pronto pro jogo
    paracritica.json-> as 18 candidatas de cada carta, pro revisor julgar
    revisao.csv     -> uma linha por carta, pra conferir com o olho
    relatorio.txt   -> o que caiu e por quê
    cache/          -> respostas cruas (re-rodar fica instantâneo)

Entrada opcional:
    revisao.json  -> as cartas fechadas pelos revisores. O TF-IDF acha o
                     vocabulário do ARTIGO, que não é o vocabulário da MESA: o
                     artigo de "cavalo" fala de dedo, altura e sangue, e ninguém
                     diz isso descrevendo um cavalo. Onde houver carta revisada,
                     ela manda; onde não houver, vale o TF-IDF cru, e o relatório
                     diz quantas estão nessa situação. Veja REVISOR.md.
"""

import argparse, csv, hashlib, json, math, os, re, sys, time, unicodedata
import urllib.parse, urllib.request
from collections import Counter

from palavras import FUNCAO, VERBAIS, META, VETADAS_CHAVE, VETADAS_PROIBIDA

UA = "JogosDaTurma/0.1 (https://github.com/leoborja/jogos-da-turma; leo@cloudarbitration.com)"
CACHE = "cache"
WIKI = "https://pt.wikipedia.org/w/api.php"
WIKT = "https://pt.wiktionary.org/w/api.php"
FREQ_URL = ("https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/"
            "content/2018/pt_br/pt_br_50k.txt")

BLOQUEIO = FUNCAO | VERBAIS | META | VETADAS_PROIBIDA
CANDIDATAS = 18          # quantas o revisor vê por carta
SEM_CACHE = False
falhas = []


def le_revisao():
    """as cartas fechadas pelos revisores. Ausente = baralho cru."""
    if not os.path.exists("revisao.json"):
        return {}, {}
    with open("revisao.json", encoding="utf-8") as fh:
        v = json.load(fh)
    return ({k.upper(): c for k, c in v.get("cartas", {}).items()},
            {k.upper(): m for k, m in v.get("descartadas", {}).items()})


# ------------------------------------------------------------------ utilidades

def sem(s):
    """minúscula, sem acento — pra comparar palavra com lista."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def radical(w):
    """corta plural e sufixo produtivo, pra 'jogador' e 'jogadores' virarem um."""
    w = sem(w)
    for s in ("acoes", "idades", "mentos", "ores", "ais", "oes", "es", "s"):
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[: len(w) - len(s)]
    return w


def perto(a, b, max_dist=1):
    """distância de edição pequena — 'câmera' e 'câmara' são a mesma palavra."""
    if abs(len(a) - len(b)) > max_dist:
        return False
    ant = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(ant[j] + 1, cur[j - 1] + 1, ant[j - 1] + (ca != cb)))
        ant = cur
    return ant[-1] <= max_dist


def tronco(w):
    """radical sem a vogal de gênero — 'branco' e 'branca' viram a mesma coisa."""
    r = radical(w)
    return r[:-1] if len(r) > 4 and r[-1] in "aoe" else r


def singulares(w):
    """candidatos a singular de w, do mais específico pro mais genérico."""
    saida = [w]
    for suf, rep in [("ões", "ão"), ("ães", "ão"), ("ais", "al"), ("éis", "el"),
                     ("eis", "il"), ("óis", "ol"), ("uis", "ul"), ("ns", "m"),
                     ("res", "r"), ("zes", "z"), ("ses", "s"), ("es", ""), ("s", "")]:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            saida.append(w[: len(w) - len(suf)] + rep)
    return saida


def baixa(url, headers=None, dados=None):
    r = urllib.request.Request(url, data=dados,
                               headers={"User-Agent": UA, **(headers or {})})
    return urllib.request.urlopen(r, timeout=60).read()


def cache_json(chave, produz):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, hashlib.md5(chave.encode()).hexdigest() + ".json")
    if os.path.exists(f) and not SEM_CACHE:
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    v = produz()
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(v, fh, ensure_ascii=False)
    time.sleep(0.06)
    return v


def api(base, **kw):
    kw.setdefault("format", "json")
    kw.setdefault("formatversion", "2")
    url = base + "?" + urllib.parse.urlencode(kw)
    return cache_json(url, lambda: json.loads(baixa(url)))


# ------------------------------------------------------------------ as bases

def lista_frequencia():
    """português falado, do mais comum pro menos. Devolve {palavra: contagem}."""
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, "frequencia_pt_br.txt")
    if not os.path.exists(f):
        print("· baixando a lista de frequência do português falado…")
        with open(f, "wb") as fh:
            fh.write(baixa(FREQ_URL))
    freq = {}
    with open(f, encoding="utf-8") as fh:
        for linha in fh:
            p = linha.split()
            if len(p) == 2 and p[0].isalpha():
                freq[p[0]] = int(p[1])
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


def dicionario():
    """{classe: conjunto de verbetes} do Wikcionário em português."""
    print("· lendo as classes gramaticais do Wikcionário…")
    d = {}
    for chave, cat in [("subst", "Categoria:Substantivo (Português)"),
                       ("adj", "Categoria:Adjetivo (Português)"),
                       ("verbo", "Categoria:Verbo (Português)")]:
        d[chave] = {w.lower() for w in categoria_wikcionario(cat) if w.isalpha()}
        print(f"    {chave}: {len(d[chave])}")
    return d


def fichas_wikipedia(titulos):
    """resumo + descrição + se é desambiguação, 20 títulos por chamada."""
    saida = {}
    for i in range(0, len(titulos), 20):
        lote = titulos[i:i + 20]
        d = api(WIKI, action="query", prop="extracts|pageprops|description",
                exintro="1", explaintext="1", exlimit="20", redirects="1",
                titles="|".join(lote))
        for p in d.get("query", {}).get("pages", []):
            saida[p["title"]] = {
                "resumo": p.get("extract", ""),
                "descricao": p.get("description", ""),
                "desambig": "disambiguation" in p.get("pageprops", {}),
                "item": p.get("pageprops", {}).get("wikibase_item", ""),
                "faltando": p.get("missing", False),
            }
        print(f"\r    fichas {min(i+20, len(titulos))}/{len(titulos)}", end="", flush=True)
    print()
    return saida


# O Tabu quer conceito, não nome próprio nem marca. Quem diz o que a coisa é
# é o Wikidata, na propriedade P31 ("instância de").
NAO_E_CONCEITO = {
    "Q5": "pessoa",
    "Q202444": "nome de batismo", "Q101352": "sobrenome",
    "Q4830453": "empresa", "Q783794": "empresa", "Q891723": "empresa de capital aberto",
    "Q6881511": "empresa", "Q431289": "marca", "Q167270": "marca",
    "Q7278": "partido político", "Q215380": "banda",
    "Q482994": "álbum", "Q7366": "canção", "Q134556": "single",
    "Q11424": "filme", "Q5398426": "série de TV", "Q571": "livro",
    "Q4167410": "desambiguação", "Q4167836": "categoria",
}


# O P31 não pega tudo: "Daniel" é figura bíblica, "Assustador" era um site.
# A descrição do Wikidata denuncia o resto.
DESCRICAO_SUSPEITA = re.compile(
    r"\b(personagem|figura b|deus |deusa |tit[ãa]|mitolog|profeta|santo|santa|rei |rainha|"
    r"imperador|papa |ap[óo]stolo|patriarca|s[íi]tio|site|website|jogo eletr|"
    r"empresa|marca|banda|[áa]lbum|can[çc][ãa]o|filme|s[ée]rie|programa de|revista|"
    r"jornal|editora|partido|clube de|equipa|equipe de|sele[çc][ãa]o|"
    # Lugar: o artigo do topônimo sequestra a palavra comum — "Guarda" vira
    # município de Portugal, "Praga" vira capital tcheca, "Palmas" vira
    # município do Tocantins. Perde-se Paris junto; vale a troca.
    r"munic[íi]pio|cidade|capital|comuna|distrito|freguesia|vila |aldeia|"
    r"estado (dos|do|da|norte-|brasileiro|federado)|prov[íi]ncia|condado|"
    r"pa[íi]s |continente|regi[ãa]o |ilha |arquip[ée]lago|"
    r"nome (pr[óo]prio|masculino|feminino|de batismo)|sobrenome|apelido|"
    r"personalidade|cantor|ator|atriz|escritor|pol[íi]tico brasileiro|futebolista)",
    re.IGNORECASE)


def tipos_wikidata(itens):
    """{item: [tipos P31]} — 50 por chamada."""
    saida = {}
    itens = [i for i in itens if i]
    for i in range(0, len(itens), 50):
        lote = itens[i:i + 50]
        d = api("https://www.wikidata.org/w/api.php", action="wbgetentities",
                props="claims", ids="|".join(lote))
        for qid, ent in d.get("entities", {}).items():
            saida[qid] = [c["mainsnak"]["datavalue"]["value"]["id"]
                          for c in ent.get("claims", {}).get("P31", [])
                          if c.get("mainsnak", {}).get("datavalue")]
        print(f"\r    tipos {min(i+50, len(itens))}/{len(itens)}", end="", flush=True)
    print()
    return saida


def artigo_wikipedia(titulo):
    """o texto corrido do artigo inteiro (o extracts completo aceita 1 por vez)."""
    d = api(WIKI, action="query", prop="extracts|description|info",
            explaintext="1", redirects="1", inprop="url", titles=titulo)
    p = d.get("query", {}).get("pages", [{}])[0]
    return {"titulo": p.get("title", titulo), "texto": p.get("extract", ""),
            "descricao": p.get("description", ""), "url": p.get("fullurl", "")}


# ------------------------------------------------------------------ a carta

def limpa(t):
    """tira parêntese (etimologia, nome estrangeiro) e título de seção."""
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"==+[^=]+==+", " ", t)
    return t


class Extrator:
    """Escolhe as proibidas. Precisa do baralho inteiro pra saber o que é banal."""

    def __init__(self, freq, dic):
        self.freq = freq
        self.total = sum(freq.values())
        self.rank = {w: i for i, w in enumerate(freq)}
        self.subst, self.adj, self.verbo = dic["subst"], dic["adj"], dic["verbo"]
        self.df = Counter()
        self.n_docs = 0

    def participio(self, w):
        m = re.match(r"^(.+?)(ados?|adas?|idos?|idas?|antes?|entes?)$", w)
        return bool(m) and any(m.group(1) + s in self.verbo for s in ("ar", "er", "ir"))

    def lema(self, w):
        """devolve (lema, é_substantivo) ou (None, None) se não for nome/adjetivo."""
        if self.participio(w):
            return None, None
        for c in singulares(w):
            if c in self.subst:
                return c, True
        for c in singulares(w):
            if c in self.adj:
                return c, False
        return None, None

    def tokens(self, texto):
        for t in re.findall(r"[a-zà-öø-ÿ]{4,}", texto.lower()):
            if sem(t) in BLOQUEIO or self.rank.get(t, 10 ** 9) > 9000:
                continue
            lema, é_subst = self.lema(t)
            if not lema or sem(lema) in BLOQUEIO:
                continue
            yield t, lema, é_subst

    def contabiliza(self, texto):
        """primeira passada: em quantos artigos do baralho cada radical aparece."""
        self.n_docs += 1
        self.df.update({radical(l) for _, l, _ in self.tokens(self.corpo(texto))})

    @staticmethod
    def corpo(texto):
        return limpa(texto)[:6000]

    def proibidas(self, alvo, texto, n=5):
        corpo = self.corpo(texto)
        lead = corpo.split("\n")[0]
        ralvo = {tronco(p) for p in re.findall(r"\w+", alvo.lower()) if len(p) > 2}
        salvo = sem(alvo)
        # nome próprio: quase sempre com maiúscula no meio da frase
        maiusc = Counter(m.group(0).lower() for m in
                         re.finditer(r"(?<![.!?]\s)(?<!^)\b[A-ZÀ-Ý][a-zà-ÿ]{3,}", corpo))
        todos = Counter(re.findall(r"[a-zà-öø-ÿ]{4,}", corpo.lower()))

        tf, forma = Counter(), {}
        for bloco, peso in ((lead, 3.0), (corpo, 1.0)):
            for t, lema, é_subst in self.tokens(bloco):
                if maiusc.get(t, 0) >= 0.6 * todos.get(t, 1):
                    continue
                r, t = radical(lema), tronco(lema)
                if any(t == x or t.startswith(x) or x.startswith(t)
                       for x in ralvo if len(x) > 3):
                    continue
                if perto(sem(lema), salvo):
                    continue
                if not é_subst:      # adjetivo puro não trava ninguém: "fresca",
                    continue         # "antigos", "necessária" não é o que se diz
                tf[r] += peso
                if r not in forma or self.freq.get(lema, 0) > self.freq.get(forma[r], 0):
                    forma[r] = lema

        saida = []
        for r, c in tf.items():
            w = forma[r]
            if w not in self.freq:
                continue
            idf_baralho = math.log((self.n_docs + 1) / (self.df[r] + 1))
            if idf_baralho <= 0.35:          # aparece em quase todo artigo
                continue
            idf_geral = math.log(self.total / self.freq[w])
            saida.append((c * (idf_baralho ** 0.6) * (idf_geral ** 0.5), w))
        saida.sort(reverse=True)
        return saida[:n]


# ------------------------------------------------------------------ o pipeline

FAIXAS = ["fácil", "média", "difícil", "osso"]


def dificuldade(pos):
    """A posição da palavra na fala. Quatro faixas, não três: de 3.500 até o
    fim da lista cabe muita coisa, e "difícil" sozinho não dizia nada."""
    if pos < 1200:
        return "fácil"
    if pos < 3500:
        return "média"
    if pos < 9000:
        return "difícil"
    return "osso"


def main():
    global SEM_CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartas", type=int, default=250, help="teto de cartas no baralho")
    ap.add_argument("--candidatos", type=int, default=20000,
                    help="até que posição da lista de frequência procurar")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--aceitar-cruas", action="store_true",
                    help="deixa entrar carta que os revisores não viram")
    a = ap.parse_args()
    SEM_CACHE = a.sem_cache

    freq = lista_frequencia()
    dic = dicionario()
    rank = {w: i for i, w in enumerate(freq)}

    # 1) candidatos: substantivo do Wikcionário, comum na fala, não vetado
    cand = []
    for w in list(freq)[: a.candidatos]:
        if len(w) < 4 or sem(w) in BLOQUEIO or sem(w) in VETADAS_CHAVE:
            continue
        if w not in dic["subst"] or w in dic["verbo"]:
            continue
        cand.append(w)
    print(f"· {len(cand)} substantivos comuns pra checar na Wikipédia")

    # 2) tem artigo de conceito? (não desambiguação, resumo de verdade)
    fichas = fichas_wikipedia([w.capitalize() for w in cand])
    aprovados = []
    for w in cand:
        f = fichas.get(w.capitalize())
        if not f or f["faltando"]:
            falhas.append((w, "sem artigo na Wikipédia")); continue
        if f["desambig"]:
            falhas.append((w, "página de desambiguação")); continue
        if len(f["resumo"]) < 350:
            falhas.append((w, f"resumo curto ({len(f['resumo'])} car.)")); continue
        if not f["descricao"]:
            falhas.append((w, "sem descrição no Wikidata")); continue
        if DESCRICAO_SUSPEITA.search(f["descricao"]):
            falhas.append((w, f"descrição de nome próprio: {f['descricao'][:40]}")); continue
        aprovados.append(w)
    print(f"· {len(aprovados)} com artigo")

    tipos = tipos_wikidata([fichas[w.capitalize()]["item"] for w in aprovados])
    conceitos = []
    for w in aprovados:
        item = fichas[w.capitalize()]["item"]
        ruim = [NAO_E_CONCEITO[t] for t in tipos.get(item, []) if t in NAO_E_CONCEITO]
        if ruim:
            falhas.append((w, f"não é conceito: {ruim[0]}")); continue
        conceitos.append(w)
    aprovados = conceitos
    print(f"· {len(aprovados)} que são conceito, não nome próprio nem marca")

    # 3) texto inteiro — em três faixas de frequência, pra existir carta difícil
    faixas = {f: [] for f in FAIXAS}
    for w in aprovados:
        faixas[dificuldade(rank[w])].append(w)
    por_faixa = max(40, int(a.cartas * 1.2))
    alvo = [w for f in faixas.values() for w in f[:por_faixa]]
    print("· candidatos por faixa: " +
          ", ".join(f"{k} {min(len(v), por_faixa)}" for k, v in faixas.items()))
    artigos = {}
    for i, w in enumerate(alvo):
        art = artigo_wikipedia(w.capitalize())
        if len(art["texto"]) >= 1800:
            artigos[w] = art
        else:
            falhas.append((w, f"artigo curto ({len(art['texto'])} car.)"))
        print(f"\r    artigos {i+1}/{len(alvo)}", end="", flush=True)
    print()

    # 4) duas passadas: primeiro o que é banal no baralho, depois a carta
    ex = Extrator(freq, dic)
    for art in artigos.values():
        ex.contabiliza(art["texto"])

    revisadas, descartadas = le_revisao()
    # Uma vez que existe revisão, carta crua não entra: ela seria justamente a
    # do fundo da faixa, que é onde mora a carta ruim. Vale um baralho menor.
    so_revisadas = bool(revisadas) and not a.aceitar_cruas
    if revisadas or descartadas:
        print(f"· revisao.json: {len(revisadas)} cartas fechadas pelos revisores, "
              f"{len(descartadas)} descartadas"
              + (" — carta crua não entra" if so_revisadas else ""))

    cartas, criticas = [], []
    for w, art in artigos.items():
        W = w.upper()
        if W in descartadas:
            falhas.append((w, "revisor descartou: " + descartadas[W])); continue
        todas = ex.proibidas(w, art["texto"], n=CANDIDATAS)
        rev = revisadas.get(W)
        if rev:
            proibidas, no_artigo = rev["proibidas"], rev.get("no_artigo", [])
            forca = [999.0] * 5          # revisada ganha de crua na hora de escolher
        else:
            # Sem revisão a carta ainda precisa passar no corte cru — senão
            # entope a fila de revisão com carta que não ia servir de todo jeito.
            if len(todas) < 5:
                falhas.append((w, "menos de 5 proibidas")); continue
            top = todas[:5]
            if top[4][0] < 0.28 * top[0][0]:
                falhas.append((w, f"5ª proibida fraca ({top[4][0]/top[0][0]:.0%} da 1ª)"))
                continue
            proibidas = [p.upper() for _, p in top]
            no_artigo = list(proibidas)   # cru: as cinco vieram do artigo
            forca = [round(s, 2) for s, _ in top]

        criticas.append({
            "palavra": W,
            "sentido": art["descricao"],
            "dificuldade": dificuldade(rank[w]),
            "url": art["url"],
            "revisada": bool(rev),
            "candidatas": [p.upper() for _, p in todas],
        })
        if not rev and so_revisadas:
            falhas.append((w, "na fila de revisão")); continue
        cartas.append({
            "palavra": W,
            "sentido": art["descricao"],
            "proibidas": proibidas,
            "no_artigo": no_artigo,
            "revisada": bool(rev),
            "forca": forca,
            "dificuldade": dificuldade(rank[w]),
            "posicao": rank[w] + 1,
            "artigo": art["titulo"],
            "url": art["url"],
        })

    # As melhores de cada faixa, em partes iguais. Sem revisão, nunca raspamos
    # mais de 70% de uma faixa: o fundo de uma faixa magra é onde mora a carta
    # ruim. Com revisão o fundo já foi olhado por gente, e o corte só jogaria
    # carta boa fora — então cai.
    escolhidas = []
    for f in FAIXAS:
        da_faixa = sorted((c for c in cartas if c["dificuldade"] == f),
                          key=lambda c: -min(c["forca"]))
        teto = len(da_faixa) if so_revisadas else int(len(da_faixa) * 0.7)
        cota = min(a.cartas // len(FAIXAS), teto)
        escolhidas += da_faixa[:cota]
        print(f"    {f}: {len(da_faixa)} boas, {cota} escolhidas")
    cartas = sorted(escolhidas, key=lambda c: c["posicao"])

    banco = {
        "gerado_em": time.strftime("%Y-%m-%d"),
        "fontes": [
            {"nome": "Wikipédia em português",
             "papel": "de onde saem as cinco proibidas de cada carta",
             "url": "https://pt.wikipedia.org", "licenca": "CC BY-SA 4.0"},
            {"nome": "Wikcionário em português",
             "papel": "diz o que é substantivo, adjetivo e verbo",
             "url": "https://pt.wiktionary.org", "licenca": "CC BY-SA 4.0"},
            {"nome": "FrequencyWords (OpenSubtitles 2018, pt-BR)",
             "papel": "escolhe as palavras-chave e mede a dificuldade",
             "url": "https://github.com/hermitdave/FrequencyWords",
             "licenca": "CC BY-SA 4.0"},
        ],
        "metodo": ("Cada carta nasce de um TF-IDF sobre o artigo da Wikipédia e "
                   "passa por três revisores que não se veem: um escreve as dez "
                   "palavras que usaria pra mesa acertar, outro as dez que lhe vêm "
                   "à cabeça, e um terceiro cruza as duas listas com as candidatas "
                   "do artigo e fecha as cinco. O ponto ao lado de uma proibida diz "
                   "que ela também aparece no artigo — o link abre e confere. "
                   "A dificuldade é a posição da palavra-chave numa lista de "
                   "frequência do português falado."),
        "cartas": [{k: v for k, v in c.items() if k != "forca"} for c in cartas],
    }
    with open("banco.json", "w", encoding="utf-8") as fh:
        json.dump(banco, fh, ensure_ascii=False, indent=1)

    # paracritica.json é a FILA da revisão: tudo que passou no funil, revisado
    # ou não, com as candidatas que ficaram de fora do corte de 5 — é lá que
    # mora o conserto. O campo "revisada" diz o que ainda falta olhar.
    criticas.sort(key=lambda c: (c["revisada"], FAIXAS.index(c["dificuldade"])))
    with open("paracritica.json", "w", encoding="utf-8") as fh:
        json.dump({"gerado_em": banco["gerado_em"],
                   "na_fila": sum(1 for c in criticas if not c["revisada"]),
                   "cartas": criticas}, fh, ensure_ascii=False, indent=1)

    with open("revisao.csv", "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["palavra", "sentido", "proibidas", "revisada", "no_artigo",
                     "5a_forca", "dificuldade", "posicao_na_fala", "artigo"])
        for c in cartas:
            wr.writerow([c["palavra"], c["sentido"], " · ".join(c["proibidas"]),
                         "sim" if c["revisada"] else "não",
                         f'{len(c["no_artigo"])}/5',
                         min(c["forca"]), c["dificuldade"], c["posicao"], c["url"]])

    with open("relatorio.txt", "w", encoding="utf-8") as fh:
        fh.write(f"gerado em {banco['gerado_em']}\n")
        fh.write(f"{len(cartas)} cartas de {len(artigos)} artigos lidos\n\n")
        por_dif = Counter(c["dificuldade"] for c in cartas)
        fh.write("dificuldade: " + ", ".join(f"{k} {v}" for k, v in por_dif.items()) + "\n")
        rev = sum(1 for c in cartas if c["revisada"])
        conf = sum(len(c["no_artigo"]) for c in cartas)
        fh.write(f"revisadas: {rev} de {len(cartas)} "
                 f"({len(cartas)-rev} ainda com as 5 do TF-IDF cru)\n")
        fh.write(f"proibidas confirmadas no artigo: {conf} de {len(cartas)*5}\n\n")
        fh.write("o que caiu e por quê\n")
        motivos = Counter(m.split("(")[0].strip() for _, m in falhas)
        for m, n in motivos.most_common():
            fh.write(f"  {n:5d}  {m}\n")
        fh.write("\ndetalhe (só os que chegaram a ter artigo lido)\n")
        for w, m in falhas:
            if "artigo curto" in m or "proibida" in m:
                fh.write(f"  {w}: {m}\n")

    rev = sum(1 for c in cartas if c["revisada"])
    print(f"\n✓ {len(cartas)} cartas em banco.json")
    print("  " + " · ".join(f"{por_dif[f]} {f}" for f in FAIXAS))
    print(f"  {rev} revisadas, {len(cartas)-rev} ainda cruas")
    print("  confira revisao.csv antes de subir")


if __name__ == "__main__":
    main()
