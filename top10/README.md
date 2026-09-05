# Top 10 — Jogos da Turma

Jogo de mesa digital: a carta traz uma pergunta cuja resposta é um ranking de
dez (“quais os países que mais exportam?”) e os jogadores vão dizendo itens que
acham que estão na lista, sem repetir.

**Jogar:** https://jogosdaturma.com.br/top10/

## A partida

Uma rodada é uma carta. Uma partida é um punhado de rodadas (3, 5, 7, 10 ou
sem fim), e o placar acumula:

| | |
|---|---|
| acertar um item | **+1** |
| sobrar de pé no fim da rodada | **+3** |
| pegar um blefe (modo sem juiz) | **+2** |

Acerto pontua mesmo pra quem cai antes do fim — senão só o último sobrevivente
pontuaria e quem jogou bem a rodada inteira sairia sem nada.

O baralho lembra o que já saiu, no navegador de quem segura o celular, então a
turma pode jogar semana que vem sem repetir carta. A memória é apagada sozinha
quando o banco é regerado (os ids mudam). Nada disso sai do aparelho.

## Os dois modos

**Com juiz** — uma pessoa segura o celular, não joga e digita o que cada um
fala. Errou, perde uma vida. Sai quem zerar.

**Sem juiz** — o celular fica no meio e ninguém vê o gabarito. O palpite fica
pendurado até alguém apertar *Contesto*. Se o palpite não valia, quem falou
perde a vida; se valia, quem contestou é que se dá mal. É o formato do
*É Top!?* (Grok Games, 2021).

## Cada carta tem um tipo de resposta

País, município, nome de pessoa, língua e família linguística. O palpite é
resolvido contra o índice **daquele tipo**, nunca contra todos: "São Paulo" é
município e é estado, e a carta pergunta de um só.

Para país e município o índice é a lista completa do mundo, então palpite que
não bate é erro de digitação e o juiz arbitra. Nome de pessoa é lista aberta —
só conhecemos os nomes que aparecem em algum ranking do IBGE, mas "Roberto" é
palpite legítimo, só não está no top 10. Nesse tipo, o que não bate conta como
erro direto, sem incomodar o juiz.

## Na hora de digitar

O juiz digita duas letras e o dropdown mostra o que bate — um toque
resolve o palpite. Ele lista **todos** os 195, não só os do gabarito: sugerir
só resposta certa entregaria a carta. Quem já foi falado aparece apagado.

Quem quiser jogar mais leve pode ligar a **lista A-Z** no começo: fica uma
gaveta com tudo do tipo da carta em ordem alfabética. Ela não marca quem está
no gabarito — é lembrete de que a coisa existe, não dica. Em carta de
município ela não aparece: 5.570 numa gaveta não ajuda ninguém.

## O banco de cartas

274 cartas em cinco temas — países, Brasil, cinema, esporte e línguas — geradas de bases abertas — nada escrito à
mão, porque carta errada quebra o jogo:

| Fonte | O que vem de lá |
|---|---|
| Banco Mundial (WDI) | 101 indicadores: economia, população, saúde, energia, meio ambiente |
| Glottolog (CLDF) | quantas línguas se fala em cada país, tamanho das famílias linguísticas |
| IBGE | os 5.570 municípios (Censo 2022) e o ranking de nomes de pessoa (Censo 2010) |
| Wikidata (SPARQL) | bilheteria de filme, capacidade de estádio, nome do país em pt-BR e os apelidos que a gente fala na mesa |

Cada carta guarda o indicador, o ano e quantos países entraram no ranking, e o
gabarito mostra o valor de cada resposta.

**Toda carta explica o que o número mede.** É a parte que encerra discussão na
mesa: por que Singapura aparece com 258% de energia importada (o denominador
desconta o combustível de navio e avião internacional, o numerador não), por
que matrícula no ensino superior passa de 100% (aluno de qualquer idade conta),
por que a Irlanda lidera passageiros de avião (a Ryanair é registrada lá). As
notas estão em `notas.py`, escritas a partir da definição oficial — que vai
junto no `banco.json`, palavra por palavra, com link pra fonte.

Carta sem nota não passa: o gerador reclama no `relatorio.txt`.

> O REST Countries, que o projeto usava para nome e apelido, foi descontinuado
> (v3.1, v4 e v5 respondem `deprecated`). Trocado por Wikidata.

## Regerar o banco

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install requests
python gerador.py
```

Saídas: `banco.json` (o que o site lê), `revisao.csv` (uma linha por carta com
o top 10 inteiro, pra conferir com o olho) e `relatorio.txt` (o que foi
descartado e por quê). O `cache/` guarda as respostas cruas — a segunda
execução é instantânea.

```
python gerador.py --listar                 # catálogo do WDI em CSV, pra achar indicadores novos
python gerador.py --manter-disputadas      # mantém carta com empate no 10º/11º
python gerador.py --incluir-territorios    # devolve Hong Kong, Porto Rico e cia
python gerador.py --min-paises 80          # exige mais cobertura por carta
python gerador.py --max-sobreposicao 0.5   # menos tolerância com carta repetida
```

Os códigos de indicador do Banco Mundial são descontinuados sem aviso. Quando
um cair, ele aparece em `relatorio.txt` — ache o substituto com `--listar` e
troque em `indicadores.py`.

## O que ficou de fora, e por quê

Vale mais não ter a carta do que ter uma que a mesa desminta:

- **Clubes com mais Brasileirões.** O Wikidata não tem as edições de 1964,
  2000, 2005, 2020, 2023 e 2024. Com isso o Palmeiras sairia com 11 títulos e
  o Corinthians com 6, e qualquer brasileiro perceberia. Copa do Brasil e
  Paulista param em 2020; o Carioca tem seis buracos. Daí a regra em
  `esporte.py`: antes de contar título, o gerador confere se a série de
  edições está inteira e chega até hoje. Só a Libertadores passa hoje.
- **Clubes com mais Libertadores.** A série está completa, mas cinco clubes
  empatam em 3 títulos bem na fronteira do 10º. Não existe top 10 honesto ali.
- **Filmes por gênero.** O `P136` do Wikidata é etiqueta frouxa: o top de
  "terror" veio com *Gravidade* e *Doutor Estranho no Multiverso da Loucura*.
- **Bola de Ouro.** Cristiano Ronaldo não aparece e Cruyff sai com 1 em vez
  de 3.

## Os filtros de qualidade

O gerador joga carta fora sozinha, porque carta ruim estraga a rodada:

- **agregado disfarçado de país** — a API devolve “Mundo” e “Zona do Euro”
  junto com os países; tudo com `region == Aggregates` cai fora, e territórios
  não soberanos (Hong Kong, Porto Rico) também.
- **ano misturado** — ranking só vale comparando o mesmo ano, então cada carta
  usa o ano mais recente com cobertura decente e ranqueia só nele.
- **empate no 10º e 11º** — o jogador acerta e “erra”. A régua depende da
  fonte: indicador do Banco Mundial é estimativa, então 0,5% ali é ruído;
  bilheteria, capacidade de estádio, censo e contagem de título são número
  exato, e ali só empate de verdade conta.
- **carta repetida** — “quem mais exporta” e “maior PIB” devolvem quase a mesma
  lista; se o top 10 repete mais de 60% de outra carta do mesmo recorte, sai
  (95 caíram aqui).
- **microestado** — todo ranking per capita vira lista de paraíso fiscal, então
  cada indicador tem um `min_pop`.
- **base pequena** — carta global precisa de pelo menos 60 países com dado.
- **fatia que estoura o próprio rótulo** — se a pergunta promete uma parte de um
  todo, o valor tem que caber entre 0 e 100%. Os indicadores sujeitos a essa
  regra estão em `FATIA_0_100`; quem estoura por definição (energia importada)
  fica de fora da lista e explica o motivo na nota da carta.
- **carta sem explicação** — toda carta precisa de uma nota dizendo o que o
  número mede. Sem isso a rodada vira discussão.

## Sinônimos

A parte mais chata não são os dados, é o juiz digital entender “EUA”,
“Holanda”, “Inglaterra”. O `banco.json` traz um índice de países com os
apelidos normalizados (minúscula, sem acento, sem pontuação) e o site resolve
o palpite contra ele antes de olhar a carta — inclusive com tolerância a erro
de digitação (“alemanya” vira Alemanha). Apelido que aponta para dois países é
descartado: apelido ambíguo é pior que apelido nenhum.

Nome que o juiz não reconhecer, anota em `APELIDOS_EXTRA` no `indicadores.py`.
Enquanto isso o botão *Foi acerto / Foi erro* deixa o juiz decidir na hora.

## Arquivos

```
index.html        o jogo (sem build, sem backend)
banco.json        as cartas + o índice de países
gerador.py        busca, filtra e monta o banco
indicadores.py    catálogo de indicadores, regiões, apelidos, vetos
linguas.py        cartas do tema línguas
revisao.csv       conferência visual
relatorio.txt     o que caiu e por quê
```
