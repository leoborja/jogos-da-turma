#!/usr/bin/env python3
"""
casas.py — o que vai em cada casa do jogo, e o que não vai em carta nenhuma.

A casa de uma carta não é opinião: é o arquivo lexicográfico em que a WordNet
de Princeton guarda aquele sentido. São 45 arquivos temáticos (noun.animal,
noun.artifact, verb.motion…), e cada synset mora em exatamente um. O que este
arquivo faz é dizer qual arquivo cai em qual casa do Imagem e Ação — e deixar
de fora os arquivos que não viram gesto (noun.quantity, verb.stative e afins).

Referência dos arquivos: https://wordnet.princeton.edu/documentation/lexnames5wn
"""

# ---------------------------------------------------------------- as casas

CASAS = [
    {
        "id": "objeto",
        "nome": "Objeto",
        "letra": "O",
        "cor": "#FFD23F",
        "o_que_e": "coisa que dá pra ver ou tocar",
        "arquivos": ["noun.artifact", "noun.food", "noun.plant", "noun.body",
                     "noun.object", "noun.substance", "noun.shape"],
    },
    {
        "id": "pessoa",
        "nome": "Pessoa, lugar ou bicho",
        "letra": "P",
        "cor": "#7FE0A5",
        "o_que_e": "gente, bicho e lugar — inclusive nome próprio",
        "arquivos": ["noun.person", "noun.animal", "noun.location"],
    },
    {
        "id": "acao",
        "nome": "Ação",
        "letra": "A",
        "cor": "#FFA552",
        "o_que_e": "verbo: coisa que se faz",
        "arquivos": ["verb.motion", "verb.contact", "verb.body", "verb.consumption",
                     "verb.competition", "verb.creation", "verb.perception",
                     "verb.change", "verb.possession", "verb.social"],
    },
    {
        "id": "dificil",
        "nome": "Difícil",
        "letra": "D",
        "cor": "#C9A7F5",
        "o_que_e": "o que não se pega com a mão: sentimento, acontecimento, estado",
        "arquivos": ["noun.feeling", "noun.event", "noun.phenomenon", "noun.state",
                     "verb.emotion"],
    },
]

# O que cada arquivo lexicográfico guarda, em português — é o que a carta
# mostra pra explicar por que caiu naquela casa.
ARQUIVOS = {
    "noun.artifact":   "coisas feitas por gente",
    "noun.food":       "comida e bebida",
    "noun.plant":      "plantas",
    "noun.body":       "partes do corpo",
    "noun.object":     "objetos naturais — rio, montanha, sol",
    "noun.substance":  "materiais e substâncias",
    "noun.shape":      "formas",
    "noun.person":     "gente",
    "noun.animal":     "bichos",
    "noun.location":   "lugares",
    "verb.motion":     "verbos de movimento",
    "verb.contact":    "verbos de tocar, bater e segurar",
    "verb.body":       "verbos do que se faz com o corpo",
    "verb.consumption": "verbos de comer, beber e consumir",
    "verb.competition": "verbos de disputa e luta",
    "verb.creation":   "verbos de fazer e criar",
    "verb.perception": "verbos de ver, ouvir e cheirar",
    "verb.change":     "verbos de mudar de estado",
    "verb.possession": "verbos de dar, receber e trocar",
    "verb.social":     "verbos do que se faz com os outros",
    "noun.feeling":    "sentimentos",
    "noun.event":      "acontecimentos",
    "noun.phenomenon": "fenômenos da natureza",
    "noun.state":      "estados",
    "verb.emotion":    "verbos do que se sente",
}

# arquivo lexicográfico -> id da casa
CASA_DO_ARQUIVO = {arq: c["id"] for c in CASAS for arq in c["arquivos"]}

# Quando a palavra tem sentido em mais de uma casa, fica com o mais concreto:
# é o que o corpo consegue mostrar. "Coração" é o órgão antes de ser o centro
# de alguma coisa.
PRIORIDADE = {"pessoa": 0, "objeto": 1, "acao": 2, "dificil": 3}


# ------------------------------------------------------- fora do baralho

# Palavrão, sexo e crueldade. A mesa é de amigos, mas o celular passa de mão em
# mão e ninguém escolhe a carta que vai receber.
IMPROPRIAS = {
    "boceta", "buceta", "caralho", "cu", "foda", "foder", "trepar", "transar",
    "punheta", "pica", "rola", "piroca", "xoxota", "peido", "peidar", "cagar",
    "bosta", "merda", "mijo", "mijar", "gozar", "gozo", "puta", "putaria",
    "prostituta", "prostituição", "vagabunda", "cachorra", "veado", "viado",
    "bicha", "traveco", "retardado", "aleijado", "mongoloide", "nazista",
    "estupro", "estuprar", "estuprador", "pedófilo", "pedofilia", "incesto",
    "masturbação", "masturbar", "orgasmo", "ejaculação", "pênis", "vagina",
    "escroto", "saco", "testículo", "seio", "peito", "bunda", "nádega",
    "suicídio", "suicidar", "enforcar", "esfaquear", "estrangular", "torturar",
    "tortura", "mutilar", "cocaína", "maconha", "heroína", "crack", "drogado",
    "viciado", "aborto", "abortar", "cadáver", "necrotério", "câncer", "tumor",
    "aids", "leucemia", "genocídio", "escravo", "escravidão", "linchamento",
}

# A palavra existe, o sentido existe, mas a carta não presta: ou é genérica
# demais pra virar gesto ("coisa", "tipo"), ou o sentido que a WordNet escolheu
# não é o que a pessoa vai ler na tela ("ala" não é asa de bicho no Brasil).
VETADAS = {
    # genérico demais
    "coisa", "coisas", "tipo", "item", "objeto", "artefato", "unidade", "parte",
    "pedaço", "conjunto", "grupo", "espécie", "exemplar", "modelo", "forma",
    "material", "matéria", "elemento", "produto", "aparelho", "instrumento",
    "dispositivo", "equipamento", "ferramenta", "máquina", "sistema", "estrutura",
    "área", "espaço", "lugar", "local", "ponto", "posição", "situação", "estado",
    "condição", "caso", "modo", "meio", "jeito", "maneira", "assunto", "questão",
    "aspecto", "detalhe", "fator", "nível", "grau", "ordem", "série", "linha",
    "corpo", "ser", "criatura", "bicho", "animal", "planta", "pessoa", "gente",
    "indivíduo", "sujeito", "figura", "cara", "alguém", "adulto", "membro",
    "alimento", "comida", "bebida", "substância", "produtos", "artigo",
    # sentido que não é o do português do dia a dia
    "ala", "anular", "digital", "cultivar", "bordo", "carolina", "cosmos",
    "constante", "are", "at", "ace", "este", "nona", "nono", "cabo", "alto",
    "altos", "alturas", "campos", "antigos", "aves", "ativos", "efeitos",
    "custos", "morais", "regras", "batidas", "adolescentes", "alimentos",
    "algas", "ervas", "cereais", "colheita", "casca", "asas", "ciúmes",
    "amo", "ama", "pena", "presa", "tira", "madre", "meter", "ferrar",
    "safar", "vale", "peça", "monte", "fonte", "quadra", "colo", "veste",
    "fumo", "dobra", "perímetro", "reta", "flanco", "saca", "arrasar",
    # posição não é lugar, e ninguém mostra "frente" com o corpo
    "frente", "lado", "cima", "baixo", "direção", "comando", "endereço",
    "zona", "área", "arredores", "borda", "canto", "ambiente", "andamento",
    # parte de bicho fica esquisita na casa do bicho
    "asa", "cauda", "bico", "pata", "chifre", "garra", "presas",
    # advérbio, pronome e afins que caíram em synset de substantivo
    "agora", "aqui", "ali", "lá", "além", "porque", "porquê", "quando", "onde",
    "hoje", "ontem", "amanhã", "sempre", "nunca", "talvez", "assim", "então",
    # tempo e medida não viram gesto
    "ano", "mês", "semana", "dia", "hora", "minuto", "segundo", "século",
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",

    # ------------------------------------------------------------------
    # Daqui pra baixo é o que sobrou depois de ler o baralho inteiro com o
    # olho. A peneira automática acerta a classe da palavra, não o que ela
    # evoca em quem lê "faça a mímica disto" numa tela.
    # ------------------------------------------------------------------

    # particípio que a máquina leu como substantivo
    "morto", "dado", "penso", "preparado", "conhecido", "acusado", "amado",
    "preso", "criado", "criada", "cria", "empregado", "encarregado",
    # adjetivo que virou substantivo e ninguém consegue mostrar
    "vão", "forte", "estranho", "querido", "louco", "humano", "responsável",
    "suspeito", "superior", "interior", "exterior", "civil", "virgem",
    "solteiro", "escolar", "novato", "clássico", "selvagem", "egoísta",
    # xingamento: a carta é sorteada, ninguém escolhe receber
    "idiota", "imbecil", "babaca", "otário", "cretino", "bobo", "tolo",
    "burro", "estúpido", "covarde", "mentiroso", "vagabundo", "bêbado",
    "criminoso", "bandido", "traidor", "escroto",
    # rótulo de povo, cor e crença não é carta de jogo de mímica
    "branco", "negro", "índio", "judeu", "cristão", "comunista", "alemão",
    "russo", "britânico", "americano", "africano", "estrangeiro", "papa",
    "bispo", "santo", "deusa", "muçulmano", "católico",
    # ponto cardeal, medida e recorte administrativo
    "norte", "sul", "leste", "oeste", "oriente", "ocidente", "dobro",
    "rumo", "rota", "ponta", "reserva", "moda", "território", "terreno",
    "distrito", "condado", "campus", "império", "vizinhança", "esconderijo",
    # coisa que não tem como mostrar
    "acesso", "arte", "trato", "tomo", "restos", "criação", "origem",
    "superfície", "cobertura", "câmara", "quinta", "guia", "descanso",
    "terapia", "mama", "hall", "grama", "passeio", "oxigênio", "metal",
    "amizade", "vírus", "plástico", "combustível", "entrada",
    # plural que entrou sozinho
    "navios", "paredes", "óculos",
    # abstração sem gesto possível, mesmo na casa Difícil
    "vez", "querer", "gostar", "potencial", "impacto", "existência",
    "imunidade", "integridade", "status", "independência", "avanço",
    "aposentadoria", "perfeição", "celebridade", "preferência",
    "contabilidade", "funcionamento", "entendimento", "ocorrência",
    "prestígio", "estima", "alteração", "condução", "consequência",
    "deficiência", "circunstância", "prioridade", "sobrevivência",
    "cenário", "empate", "placar", "ressonância", "transe", "espectro",
    "vácuo", "feixe", "líquido", "isolamento", "impasse", "desemprego",
    "cativeiro", "hipnose", "tirania", "umidade", "resultado", "presença",
    "início", "ausência", "gravidade", "equilíbrio", "transformação",
    "melhora", "prosperidade", "infelicidade", "ressentimento",
    "nervosismo", "cansaço", "prejuízo", "estresse", "incômodo", "urgência",
    "intimidade", "sujeira", "clima", "efeito", "episódio", "ocasião",
    "chance", "oportunidade", "segurança", "pressão", "dificuldade",
    "reputação", "vaidade", "desprezo", "temporal", "auge", "matrimônio",
    # doença e sangue: dá carta ruim e mesa constrangida
    "doença", "infecção", "hemorragia", "sangramento", "lesão", "ferimento",
    "convulsão", "epidemia", "poluição", "contaminação", "sintoma",
    "inchaço", "machucado", "distúrbio", "transtorno", "gripe", "resfriado",
    # verbo sem gesto: ninguém faz a mímica de "utilizar"
    "usar", "utilizar", "parecer", "buscar", "criar", "imaginar", "demorar",
    "devolver", "executar", "expor", "demonstrar", "desfazer", "torcer",
    "recuar", "errar", "detectar", "dispor", "caber", "monitorar",
    "descarregar", "repassar", "consumir", "ocultar", "reproduzir",
    "destacar", "renovar", "traçar", "improvisar", "manipular", "desfrutar",
    "concorrer", "distribuir", "revistar", "infiltrar", "encobrir",
    "regressar", "retornar", "largar", "botar", "enfiar", "instalar",
    "transportar", "compor", "arruinar", "afastar", "soltar", "cruzar",
    "ressuscitar", "evacuar", "imprimir", "copiar", "exibir", "sequestrar",
    "ferrar", "safar",
    # grafia de Portugal quando o baralho já tem a do Brasil
    "contacto", "stress", "acção",
    # verbo de mudar, de trocar e de conviver que não sai do papel: entram na
    # casa Ação pelo arquivo certo, mas não têm gesto que a mesa reconheça
    "tornar", "iniciar", "eliminar", "completar", "diminuir", "reduzir",
    "regular", "ocorrer", "surgir", "facilitar", "adaptar", "refazer",
    "retomar", "reverter", "revisar", "aprontar", "isolar", "comparecer",
    "calhar", "complicar", "fortalecer", "ativar", "remover", "retirar",
    "recomeçar", "acostumar", "melhorar", "começar", "aparecer", "magoar",
    "encaixar", "refrescar", "possuir", "render", "dispensar", "financiar",
    "descontar", "beneficiar", "retribuir", "partilhar", "ceder", "fornecer",
    "poupar", "recuperar", "revelar", "cobrar", "subornar", "tentar", "agir",
    "impedir", "permitir", "convencer", "participar", "cumprir", "envolver",
    "cometer", "cancelar", "negociar", "testar", "processar", "falhar",
    "interferir", "cooperar", "esforçar", "auxiliar", "honrar", "romper",
    "armar", "governar", "bloquear", "obrigar", "promover", "administrar",
    "impor", "intervir", "colaborar", "inscrever", "redimir", "sabotar",
    "abusar", "gerenciar", "acionar", "travar", "recrutar", "assistir",
    "praticar", "despedir", "cumprir",
}
