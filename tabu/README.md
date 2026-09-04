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
- Cada acerto vale **1 ponto**. Falar proibida ou pular dá **1 ponto pro
  adversário**. Com mais de dois times não existe "o adversário", então o erro
  tira 1 ponto de quem estava descrevendo — a tela avisa qual regra está valendo.
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
pessoa usaria pra explicar isto?* A resposta é medida, não opinião:

| o quê | de onde | como |
| --- | --- | --- |
| **palavra-chave** | [FrequencyWords][freq] (OpenSubtitles pt-BR) + [Wikcionário][wikt] | substantivo comum na fala, com artigo de conceito na Wikipédia |
| **proibidas** | [Wikipédia em português][wiki] | os cinco substantivos mais característicos do artigo |
| **sentido** | Wikidata | a descrição curta, que diz de qual acepção a carta fala |
| **dificuldade** | FrequencyWords | a posição da palavra-chave na lista de frequência |

"Mais característico" é TF-IDF: conta quanto a palavra aparece no artigo (com o
primeiro parágrafo pesando o triplo) e desconta o quanto ela é banal — tanto no
resto do baralho quanto no português falado. Palavra que aparece em todo artigo
não caracteriza nada.

O que o gerador joga fora antes de pontuar: palavra de função, forma verbal,
particípio, meta-texto de enciclopédia (etimologia, gentílico, unidade), nome
próprio (detectado pela maiúscula no meio da frase) e qualquer palavra parecida
demais com a própria palavra-chave — `CÂMERA` não pode ter `CÂMARA` como
proibida. Página de desambiguação, pessoa, marca, partido e personagem caem
antes, pelo `P31` do Wikidata e pela descrição.

[freq]: https://github.com/hermitdave/FrequencyWords
[wikt]: https://pt.wiktionary.org
[wiki]: https://pt.wikipedia.org

## Refazer o baralho

```bash
python3 gerador.py                 # 99 cartas, 33 de cada dificuldade
python3 gerador.py --cartas 150    # mais cartas
python3 gerador.py --sem-cache     # ignora cache/ e rebaixa tudo
```

Saídas: `banco.json` (o que o jogo lê), `revisao.csv` (uma linha por carta, pra
conferir com o olho) e `relatorio.txt` (o que caiu e por quê). O `cache/` guarda
as respostas cruas das APIs, então re-rodar é instantâneo.

**Confira o `revisao.csv` antes de subir.** Nenhum filtro pega tudo: quando
aparecer carta ruim, o veto entra no `palavras.py` — é lá que moram as listas
fechadas (palavra de função, forma verbal, meta-texto, vetos e palavrão).

## Os arquivos

```
index.html    o jogo
banco.json    o baralho — gerado, não edite à mão
gerador.py    monta o baralho a partir das bases abertas
palavras.py   as listas fechadas: função, verbo, meta-texto, vetos
revisao.csv   uma linha por carta, pra revisar
relatorio.txt o que caiu do funil e por quê
cache/        respostas cruas das APIs (fora do git)
```
