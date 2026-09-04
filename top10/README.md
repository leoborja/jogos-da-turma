# Top 10 — Jogos da Turma

Jogo de mesa digital: a carta traz uma pergunta cuja resposta é um ranking de
dez (“quais os países que mais exportam?”) e os jogadores vão dizendo itens que
acham que estão na lista, sem repetir.

**Jogar:** https://leoborja.github.io/jogos-da-turma/

## Os dois modos

**Com juiz** — uma pessoa segura o celular, não joga e digita o que cada um
fala. Errou, perde uma vida. Sai quem zerar.

**Sem juiz** — o celular fica no meio e ninguém vê o gabarito. O palpite fica
pendurado até alguém apertar *Contesto*. Se o palpite não valia, quem falou
perde a vida; se valia, quem contestou é que se dá mal. É o formato do
*É Top!?* (Grok Games, 2021).

## O banco de cartas

249 cartas, temas países e línguas, geradas de bases abertas — nada escrito à
mão, porque carta errada quebra o jogo:

| Fonte | O que vem de lá |
|---|---|
| Banco Mundial (WDI) | 101 indicadores: economia, população, saúde, energia, meio ambiente |
| Glottolog (CLDF) | quantas línguas se fala em cada país, tamanho das famílias linguísticas |
| Wikidata (SPARQL) | nome do país em pt-BR e os apelidos que a gente fala na mesa |

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

## Os filtros de qualidade

O gerador joga carta fora sozinha, porque carta ruim estraga a rodada:

- **agregado disfarçado de país** — a API devolve “Mundo” e “Zona do Euro”
  junto com os países; tudo com `region == Aggregates` cai fora, e territórios
  não soberanos (Hong Kong, Porto Rico) também.
- **ano misturado** — ranking só vale comparando o mesmo ano, então cada carta
  usa o ano mais recente com cobertura decente e ranqueia só nele.
- **empate no 10º e 11º** — se a diferença é menor que 0,5%, o jogador acerta e
  “erra”. Carta descartada (55 caíram aqui).
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
