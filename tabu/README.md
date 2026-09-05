# Tabu

Faça seu time acertar a palavra sem dizer nenhuma das cinco proibidas.

O celular passa de mão em mão: quem descreve segura, e alguém do time seguinte
olha a mesma tela pra pegar quem falar proibida — é o papel da campainha no jogo
de caixa.

## As regras

Conferidas nas [instruções oficiais da Hasbro][hasbro] e na
[Wikipédia][wikipedia]:

- **Não vale** dizer a palavra, as cinco proibidas, nem pedaço, plural,
  conjugação, sigla ou rima de nenhuma delas.
- **Não vale** mímica, gesto nem imitar som. Só falar.
- Cada acerto vale **1 ponto**. Pular dá **1 ponto pro adversário**, e no jogo
  de caixa falar proibida também. Com mais de dois times não existe "o
  adversário", então o erro tira 1 ponto de quem estava descrevendo — a tela
  avisa qual regra está valendo.
- Duas coisas a mesa escolhe antes de começar: **quantos pulos cabem numa
  rodada** (padrão 1) e **o que falar proibida custa** — ponto pro adversário
  (oficial), só queimar a carta, ou acabar a rodada na hora.
- Acaba quando todo time descreveu o mesmo número de vezes.

O tempo padrão é 1 minuto, como a ampulheta da caixa.

[hasbro]: https://instructions.hasbro.com/en-us/instruction/taboo-game-instructions-manual
[wikipedia]: https://pt.wikipedia.org/wiki/Tabu_(jogo)

## De onde vêm as cartas

Não existe baralho de Tabu aberto em português — o único conjunto do gênero
([Kovah/Taboo-Data](https://github.com/Kovah/Taboo-Data)) só tem alemão e inglês.
Então o baralho é **gerado**, não escrito à mão, e cada carta carrega o link de
onde saiu.

A pergunta que a carta responde é: *quais são as cinco palavras que qualquer
pessoa usaria pra explicar isto?*

| o quê | de onde |
| --- | --- |
| **palavra-chave** | [FrequencyWords][freq] (OpenSubtitles pt-BR) + [Wikcionário][wikt]: substantivo comum na fala, com artigo de conceito na Wikipédia |
| **candidatas** | [Wikipédia em português][wiki]: as 18 palavras mais características do artigo, por TF-IDF |
| **proibidas** | o cruzamento de duas listas feitas às cegas com essas candidatas — veja [REVISOR.md](REVISOR.md) |
| **sentido** | Wikidata: a descrição curta, que diz de qual acepção a carta fala |
| **dificuldade** | FrequencyWords: a posição da palavra-chave na lista de frequência — `fácil` até a 1.200ª, `média` até a 3.500ª, `difícil` até a 9.000ª, `osso` daí pra baixo |

"Mais característico" é TF-IDF: conta quanto a palavra aparece no artigo (com o
primeiro parágrafo pesando o triplo) e desconta o quanto ela é banal — tanto no
resto do baralho quanto no português falado.

### Por que o TF-IDF não basta

Ele acha o vocabulário do **artigo**, que não é o vocabulário da **mesa**:

```
CAVALO → DEDO · ALTURA · IDADE · SANGUE · CRIATURA
```

`DEDO` está lá porque o casco é um dedo; `SANGUE`, por causa de puro-sangue.
São verdades do artigo que ninguém fala numa mesa — a carta existe e não proíbe
nada. Do outro lado, `AVIÃO` era a 15ª candidata de `AEROPORTO` e ficava fora
do corte.

Por isso cada carta passa por três revisores que não se veem: um escreve as dez
palavras que usaria pra fazer a mesa acertar, outro as dez que lhe vêm à cabeça
(com sinônimos), e um terceiro cruza as duas listas com as candidatas do artigo
e fecha as cinco. O método inteiro está em **[REVISOR.md](REVISOR.md)**.

Com isso, `CAVALO` vira `ANIMAL · MONTAR · ÉGUA · CRINA · SELA`, e o **ponto**
ao lado de uma proibida na tela diz que aquela também aparece no artigo — o
link da carta abre e confere.

O que o gerador joga fora antes de pontuar: palavra de função, forma verbal,
particípio, meta-texto de enciclopédia (etimologia, gentílico, unidade), nome
próprio (detectado pela maiúscula no meio da frase) e qualquer palavra parecida
demais com a própria palavra-chave — `CÂMERA` não pode ter `CÂMARA` como
proibida. Só substantivo vira proibida: adjetivo não trava ninguém — ninguém
perde a vez por dizer "fresca".

Página de desambiguação, pessoa, marca, partido, personagem e **topônimo** caem
antes, pelo `P31` do Wikidata e pela descrição. O topônimo importa mais do que
parece: sem esse filtro, `GUARDA` vira o município de Portugal, `PRAGA` vira a
capital tcheca e `PALMAS` vira a capital do Tocantins — o artigo sequestra a
palavra comum. Perde-se `PARIS` junto, e vale a troca.

[freq]: https://github.com/hermitdave/FrequencyWords
[wikt]: https://pt.wiktionary.org
[wiki]: https://pt.wikipedia.org

## Refazer o baralho

```bash
python3 gerador.py                 # quatro faixas, em partes iguais
python3 gerador.py --cartas 400    # sobe o teto por faixa
python3 gerador.py --sem-cache     # ignora cache/ e rebaixa tudo
```

`--cartas` é teto **por faixa**, não total. A faixa "fácil" é finita — só
existem tantas palavras muito comuns —, então pedir mais cartas engorda as
faixas de baixo, não ela. Sem revisão, nunca se raspa mais de 70% de uma faixa,
porque o fundo de uma faixa magra é onde mora a carta ruim; com revisão o corte
cai, já que o fundo passou por olho humano.

O `paracritica.json` é a **fila da revisão**: sai ordenado com o que ainda não
foi revisado primeiro, e o campo `revisada` diz o que falta.

Saídas: `banco.json` (o que o jogo lê), `revisao.csv` (uma linha por carta, pra
conferir com o olho) e `relatorio.txt` (o que caiu e por quê). O `cache/` guarda
as respostas cruas das APIs, então re-rodar é instantâneo.

Depois de gerar, rode a revisão (agentes em paralelo, um lote cada) e funda:

```bash
python3 juntar_revisao.py          # revisao/lote-*-final.json -> revisao.json
python3 gerador.py                 # remonta usando as cartas revisadas
```

**Confira o `revisao.csv` antes de subir** — ele diz, por carta, se ela é
revisada e quantas das cinco a Wikipédia confirma. Quando aparecer carta ruim
que nem a revisão pegou, o veto entra no `palavras.py`, que é onde moram as
listas fechadas (palavra de função, forma verbal, meta-texto, vetos e palavrão).

## Os arquivos

```
index.html        o jogo
banco.json        o baralho — gerado, não edite à mão
gerador.py        monta o baralho a partir das bases abertas
palavras.py       as listas fechadas: função, verbo, meta-texto, vetos
REVISOR.md        o método dos três revisores
paracritica.json  as 18 candidatas de cada carta — a entrada da revisão
revisao/          os lotes dos agentes, um arquivo por etapa
juntar_revisao.py funde os lotes e confere o que agente nenhum confere
revisao.json      as cartas fechadas — a entrada do gerador na 2ª volta
revisao.csv       uma linha por carta, pra conferir com o olho
relatorio.txt     o que caiu do funil e por quê
cache/            respostas cruas das APIs (fora do git)
```

As definições dos três agentes ficam em `.claude/agents/tabu-*.md`.
