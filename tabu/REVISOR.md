# Como as cartas do Tabu são revisadas

## O buraco

As proibidas começam num TF-IDF sobre o artigo da Wikipédia. Isso acha o
vocabulário do **artigo**, que não é o vocabulário da **mesa**:

```
CAVALO → DEDO · ALTURA · IDADE · SANGUE · CRIATURA
```

Nenhuma dessas cinco atrapalha ninguém. Quem descreve diz "animal que você
monta", "tem crina", "a fêmea é a égua" — e passa por cima da carta inteira.
A carta existe, mas não proíbe nada.

`DEDO` está lá porque o casco é um dedo. `SANGUE`, por causa de puro-sangue.
São verdades do artigo que ninguém fala numa mesa. E do outro lado: `AVIÃO`
estava na 15ª candidata de `AEROPORTO` e ficava de fora do corte.

Nenhum filtro automático resolve isso, porque a informação que falta — o que
uma pessoa **diria** — não está no artigo.

## As três etapas

O baralho passa por três etapas que não se veem:

| etapa | pergunta | o que produz |
| --- | --- | --- |
| **descritor** | "você tem 10 segundos pra mesa acertar. O que você fala?" | 10 palavras de produção |
| **associador** | "o que vem à cabeça? Inclua sinônimos." | 10 palavras de associação livre |
| **juiz** | "proibir isso tira uma saída de verdade?" | as 5 da carta |

Descritor e associador rodam **em paralelo e às cegas**: um não vê o outro, e
nenhum dos dois vê as candidatas do artigo. É isso que faz o cruzamento valer
alguma coisa — se as duas cabeças chegam na mesma palavra fazendo tarefas
mentais diferentes, aquela palavra é mesmo o que a mesa usa.

São tarefas diferentes de propósito. Dois agentes com o mesmo prompt dão a
mesma lista duas vezes, e duas listas iguais não são duas listas. Descrever e
associar são coisas distintas: o descritor dá `animal`, `montar`, `patas`; o
associador dá `corcel`, `montaria`, `faroeste`. O sinônimo quase sempre só
aparece na associação livre.

O juiz recebe as duas listas **mais** as 18 candidatas do artigo, e escolhe 5.
Prioridade: o que as duas listas cegas apontaram junto, depois o que fecha
rotas diferentes, depois a primeira palavra que sairia. As candidatas do artigo
entram como **desempate e confirmação** — o juiz anota quais das 5 escolhidas
aparecem no artigo, e é isso que a carta mostra como conferível.

## As seis rotas

Uma carta boa fecha as saídas. Quem descreve pega uma destas:

| rota | exemplo com CAVALO |
| --- | --- |
| **categoria** — o que a coisa é | "é um animal" |
| **função** — pra que serve, o que faz | "serve pra montar", "puxa carroça" |
| **parte** — do que é feita, o que tem | "crina", "quatro patas", "casco" |
| **associação** — o que vem junto | "égua", "ferradura", "jóquei" |
| **cenário** — onde aparece | "fazenda", "faroeste", "hipódromo" |
| **sinônimo** — outro nome | "corcel", "montaria" |

Não precisa fechar as seis. Precisa fechar as que a mesa usaria primeiro —
deixar a rota mais óbvia aberta arruína a carta por melhores que sejam as
outras quatro. E cinco sinônimos da mesma ideia também desperdiçam a carta:
quem descreve troca de rota e passa.

## O que muda na promessa da carta

Antes, a carta prometia: *as proibidas são as palavras mais características do
artigo da Wikipédia*. Verificável, e produzia o `CAVALO`.

Agora promete: *as proibidas são o consenso de duas listas feitas às cegas, e
estas aqui a Wikipédia confirma*. O link do artigo continua na carta, e o campo
`no_artigo` diz quais das cinco estão lá.

É uma promessa menor e honesta. Uma carta de Tabu não afirma um fato do mundo
— afirma que aquelas cinco são as palavras óbvias. Quem afirma isso é quem
jogou; o artigo confirma parte, e a carta diz qual parte.

## Rodar a revisão

```bash
python3 gerador.py                       # gera banco.json e paracritica.json
```

Depois, para cada lote de ~45 cartas, em paralelo:

```
tabu-descritor    índices A..B  →  tabu/revisao/lote-N-descritor.json
tabu-associador   índices A..B  →  tabu/revisao/lote-N-associador.json
```

Quando os dois terminarem o mesmo lote:

```
tabu-juiz  os dois arquivos  →  tabu/revisao/lote-N-final.json
```

E no fim:

```bash
python3 juntar_revisao.py                # funde os lotes em revisao.json
python3 gerador.py                       # remonta o baralho já revisado
```

O `gerador.py` lê `revisao.json`: onde houver carta fechada, ele usa as 5 do
juiz; onde houver descarte, a carta sai. Carta que o juiz não viu continua com
as 5 do TF-IDF, e o `relatorio.txt` diz quantas estão nessa situação.

## Casos que enganam

- **Palavra técnica correta.** `VENTRÍCULO` em `CORAÇÃO`: verdadeira, e a mesa
  não usa. Não serve.
- **Palavra de seção histórica.** `JUDEU` em `TATUAGEM`, `ATRIZ` em `JANEIRO`:
  vêm de "história de" e "nascidos em". Não servem.
- **Palavra de tabela.** `TONELADA`, `PRODUTOR`: vêm da seção de produção.
- **Acepção que a mesa não conhece.** `LANÇAMENTO` como ato tributário,
  `CALADO` como profundidade de navio. Descarte a carta.
- **A carta já está boa.** A maioria está. Não invente serviço.
