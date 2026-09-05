# Bandeiras — Jogos da Turma

A bandeira aparece na tela, você digita de quem ela é. O celular passa de mão
em mão e cada carta, depois de resolvida, conta a história da bandeira.

**Jogar:** https://jogosdaturma.com.br/bandeiras/

## A partida

Cada um joga a sua vez, com o celular na mão. Aparece a bandeira, você digita o
país — o campo completa a partir de duas letras e aguenta dedo trocado
("dinamarcaa" cai na Dinamarca).

| | |
|---|---|
| acertar sem dica | **3** |
| acertar com uma dica | **2** |
| acertar com duas dicas | **1** |
| errar ou passar | **0** |

As dicas vêm da carta, nunca inventadas: continente, depois capital (ou
população, para o punhado de territórios que não tem capital no Wikidata), e
"não é país" quando for território.

**Sozinho vale.** Sem ninguém cadastrado a partida começa como "Você" e a tela
de passar o celular some. É o mesmo jogo, contra o próprio placar.

O celular lembra o que já saiu, no navegador de quem segura o aparelho, então a
turma pode jogar de novo semana que vem sem repetir bandeira. A memória é
apagada sozinha quando o banco é regerado. Nada disso sai do aparelho.

## O que a mesa escolhe antes de começar

**De onde saem** — mundo todo, ou um continente só.

**Quem entra** — só os 195 países, ou os 195 mais os territórios.

**Régua** — tudo, ou só a metade mais lida. Essa segunda merece explicação, e a
tela do jogo dá ela por extenso: é a metade do recorte cujo artigo foi mais
lido **na Wikipédia em português** nos últimos 12 meses. Mede o quanto o mundo
lusófono olha pra aquele lugar — não o quanto a bandeira é difícil. Por isso
Cabo Verde aparece no topo da lista, à frente da França: é país de língua
portuguesa, e quem lê Wikipédia em português lê sobre ele. A régua serve pra
tirar Tokelau e Ilha Norfolk da mesa, não pra dizer que a França é difícil.

## O baralho

**240 cartas: 195 países e 45 territórios.** O universo é a **ISO 3166-1
alpha-2**, a lista de códigos de duas letras que o mundo usa pra identificar
lugar. Os 195 são os 193 da ONU mais o Vaticano e a Palestina, que são
observadores — lista fechada, ninguém aqui decidindo o que é país.

| Fonte | O que vem de lá |
|---|---|
| Wikidata (SPARQL) | quem tem código ISO, nome em português, apelidos, capital, continente, população, data de adoção da bandeira |
| Wikimedia Commons | a imagem — PNG renderizado do SVG oficial, o mesmo arquivo que a Wikipédia usa |
| Wikipédia lusófona | o parágrafo que explica a bandeira, com link pro artigo (237 das 240 cartas têm) |
| Pageviews API | quanto o artigo do país foi lido em português nos últimos 12 meses — é a régua de "mais fácil" |

As 240 bandeiras ficam em `img/`, dentro do repositório, e somam 1,5 MB depois
do `pngquant`. É de propósito: o jogo não depende de CDN nenhum pra rodar.

## Bandeira que não vira carta

Carta cuja resposta certa o jogo marcaria como errada não entra. São três
situações, e o gerador imprime cada corte com o motivo:

**Bandeira repetida (6).** Guiana Francesa, Guadalupe e Saint-Martin hasteiam a
bandeira da França; Svalbard e a Ilha Bouvet, a da Noruega; as Ilhas Heard e
McDonald, a da Austrália. Fica só o país soberano.

**Bandeira que não existe (2).** A Antártica não tem bandeira oficial — o
Wikidata devolve a do Tratado Antártico, que é outra coisa. As Ilhas Menores dos
EUA usam a americana. (Bonaire, Santo Eustáquio e Saba não chegam nem a ser
cortadas: não têm bandeira comum, então o Wikidata não tem imagem pra elas e a
consulta já não as traz.)

**Código que a ISO não atribuiu a ninguém (5).** Ascensão, Clipperton, Sark,
Diego Garcia e Tristão da Cunha têm código *excepcionalmente reservado*, não
atribuído. Ficam de fora porque o universo é a lista oficial.

A exceção documentada é o **Kosovo**: XK não é código oficial, é o de uso livre
que a União Europeia, o FMI e os bancos adotaram. Entra como território, porque
é um lugar com bandeira própria que a mesa reconhece — e a carta diz o que ele é.

## As bandeiras gêmeas

Duas bandeiras do baralho são a mesma coisa numa tela de celular:

- **Indonésia e Mônaco** — vermelho sobre branco, muda só a proporção (2:3 e 4:5).
- **Romênia e Chade** — o mesmo tricolor vertical; o azul do Chade é um tom mais
  escuro, e é só isso. Nem a ONU separou as duas quando o Chade reclamou, em 2004.

Nesses quatro casos **as duas respostas valem o ponto**, e a carta abre
explicando por quê. Exigir que alguém distinguisse seria o jogo mentindo que a
pessoa errou.

## Onde a fonte precisou de remendo

Cinco lugares no `gerador.py` têm dado escrito à mão. Todos estão comentados no
código, e todos existem porque a fonte tem buraco — nenhum é opinião nossa:

- **`EXCECOES`** — a cadeira da Dinamarca na ONU está no item *Reino da
  Dinamarca*, que não tem código ISO; o código está em *Dinamarca*. Sem essa
  linha o baralho teria 194 países. O Kosovo está aqui pelo motivo de cima.
- **`CORRECOES`** — o Wikidata escreve "Groelândia" com erro de digitação, e usa
  o nome longo de tratado onde a mesa fala o curto ("Reino dos Países Baixos",
  "República Popular da China").
- **`APELIDOS`** — "holanda", "eua", "kiribati", "bahrein": o que alguém digita
  de verdade no celular e o `altLabel` não tem.
- **`VETADOS`** e **`GEMEAS`** — as duas listas explicadas nas seções acima.

**A proporção da bandeira ficou de fora da carta.** O Wikidata mistura as
convenções entre um item e outro: a Romênia aparece como "2:3" e o Chade como
"3:2" para bandeiras do mesmo formato. Número que não dá pra afirmar direito não
vai pra carta. Onde a proporção importa mesmo — nas gêmeas — ela está escrita à
mão, conferida na especificação oficial de cada uma.

## Regerar o banco

```bash
cd bandeiras
python3 gerador.py
```

Baixa o que faltar, passa o `pngquant` nas imagens novas e reescreve o
`banco.json`. As respostas das APIs ficam em `cache/` (que o git ignora), então
rodar de novo é quase instantâneo — apague o `cache/` pra buscar tudo outra vez.
Bandeira que saiu do baralho tem o arquivo removido de `img/` sozinha.

O `pngquant` é opcional: sem ele o gerador avisa e segue com o PNG original,
que ocupa umas quatro vezes mais.

## Testar antes de subir

```bash
cd ..
python3 -m http.server 8090
```

`fetch` não funciona em `file://` — tem que servir por HTTP. Confira que a base
lista o jogo, que a bandeira aparece, que o autocomplete acha país por duas
letras e que o console fica limpo.
