# Imagem e Ação

Desenhe a palavra e faça seu time acertar antes do tempo.

O celular sorteia a carta, guarda o segredo e conta o tempo. O desenho é no
papel — o jogo não desenha nada por você.

## As regras

Conferidas nas [regras do Pictionary][regras] e na
[ficha do Imagem & Ação na Ludopedia][ludopedia]:

- Quem desenha **não pode** escrever letra, número ou símbolo, nem fazer
  risquinho pra contar as letras da palavra.
- **Não pode** falar, fazer mímica, apontar pra coisas da sala nem desenhar
  outra coisa pra dar dica.
- Acertou dentro do tempo, **1 ponto**.
- Na rodada **todos jogam**, um de cada time desenha a mesma palavra ao mesmo
  tempo, e o ponto é do primeiro time que acertar. A mesa escolhe de quanto em
  quanto tempo isso acontece.
- Acaba quando todo time desenhou o mesmo número de vezes. Ganha quem tiver
  mais pontos.

O tempo padrão é 1 minuto, como a ampulheta da caixa.

Duas coisas a mesa escolhe antes de começar: **quantas palavras cabem numa
rodada** — uma só, como na caixa, ou quantas der no tempo — e **quantas casas
entram no baralho**.

Na caixa se anda num tabuleiro e a categoria da vez sai da casa em que o peão
está. Aqui não tem tabuleiro: a categoria vem escrita na carta e o placar é de
pontos. O resto é igual.

[regras]: https://gamerules.com/rules/pictionary/
[ludopedia]: https://ludopedia.com.br/jogo/imagem-acao

## As quatro casas

| Letra | Casa | O que cai nela |
|---|---|---|
| **O** | Objeto | coisa que dá pra ver ou tocar |
| **P** | Pessoa, lugar ou bicho | gente, bicho e lugar |
| **A** | Ação | verbo: coisa que se faz |
| **D** | Difícil | o que não se pega com a mão: sentimento, acontecimento, estado |

A casa não é palpite de quem escreveu o baralho. A WordNet de Princeton guarda
cada sentido em exatamente um de 45 [arquivos lexicográficos][lexnames] —
`noun.artifact`, `noun.animal`, `verb.motion` —, e `casas.py` diz qual arquivo
cai em qual casa. A carta mostra a cadeia que prova: *chave → aparato →
apetrecho → artefato*.

É por isso que **rio** e **montanha** caem em Objeto, e não em lugar: a WordNet
os guarda em `noun.object`, o arquivo dos objetos naturais. A carta diz isso na
cara, em vez de esconder.

Quando a palavra tem sentido em mais de uma casa, vale o sentido mais visto no
corpus etiquetado de Princeton e, no empate, a casa mais concreta — é a que dá
desenho. "Coração" é o órgão antes de ser o centro de alguma coisa.

[lexnames]: https://wordnet.princeton.edu/documentation/lexnames5wn

## De onde vêm as cartas

| Base | Papel | Licença |
|---|---|---|
| [OpenWordnet-PT](https://github.com/own-pt/openWordnet-PT) | as palavras em português, a cadeia de hiperônimos e parte das definições | CC BY 4.0 |
| [WordNet 3.0](https://wordnet.princeton.edu/) | o arquivo lexicográfico que decide a casa, e qual é o sentido de sempre | licença WordNet 3.0 |
| [Wikcionário](https://pt.wiktionary.org) | confirma a classe da palavra, dá o resto das definições e é o link de conferir | CC BY-SA 4.0 |
| [FrequencyWords](https://github.com/hermitdave/FrequencyWords) (OpenSubtitles 2018, pt-BR) | diz se a palavra é conhecida e mede a raridade | CC BY-SA 4.0 |

O caminho de uma carta:

1. Todo lema em português da OpenWordnet-PT que seja **uma palavra só**, esteja
   na lista de frequência do português falado e o Wikcionário confirme como
   **substantivo ou verbo no infinitivo**.
2. O sentido que vira carta é o **mais visto** no corpus de Princeton. Se ele
   responde por menos da metade das aparições da palavra, a carta cai: quem ler
   "asa" vai pensar em outra coisa.
3. A casa sai do arquivo lexicográfico desse sentido.
4. A raridade é a posição na lista de frequência: **comum** até a 2000ª,
   **conhecida** até a 7000ª, **rara** depois disso.
5. O teto por casa mantém o baralho equilibrado, pegando as mais comuns
   primeiro.

O que a peneira automática não pega está em `casas.py`, na mão e comentado:
particípio que a máquina leu como substantivo (*morto*, *dado*), xingamento,
rótulo de povo e de crença, abstração sem desenho possível (*integridade*,
*status*) e verbo sem gesto (*utilizar*, *parecer*).

## Refazer o baralho

```bash
python3 gerador.py                  # gera banco.json, revisao.csv e relatorio.txt
python3 gerador.py --por-casa 200   # muda o teto de cartas por casa
python3 gerador.py --topo 25000     # aceita palavra mais rara
python3 gerador.py --sem-cache      # rebaixa tudo
```

A primeira rodada baixa ~50 MB pro `cache/` (a WordNet de Princeton, a
OpenWordnet-PT, a lista de frequência e as categorias do Wikcionário). Depois
disso é instantâneo.

- `banco.json` — o baralho que o jogo lê.
- `revisao.csv` — uma linha por carta, pra ler com o olho antes de subir.
- `relatorio.txt` — quantas cartas por casa, quantas caíram e por quê.

## Os arquivos

```
index.html    o jogo
banco.json    o baralho gerado
gerador.py    monta o baralho a partir das bases
casas.py      o que vai em cada casa e o que não vai em carta nenhuma
revisao.csv   o baralho em tabela, pra conferir
relatorio.txt o que entrou e o que caiu
cache/        as bases cruas (não vai pro git)
```
