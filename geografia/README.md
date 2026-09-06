# Geografia — Jogos da Turma

O celular passa de mão em mão. Na sua vez a carta pergunta — que país é essa
bandeira, qual a capital daqui, de que país é essa capital — e você digita.
Depois a carta abre e conta o que ela sabe.

**Jogar:** https://jogosdaturma.com.br/geografia/

> Este jogo nasceu como **Bandeiras**, em `/bandeiras/`. Quando ganhou o módulo
> de capitais o nome ficou estreito e a pasta virou `geografia/`. A pasta
> `bandeiras/` continua na raiz com um redirecionamento, pra não quebrar o link
> que já circulou — ela não tem `jogo.json`, então o `atualizar_jogos.py` a
> ignora e ela não aparece na base.

## Os três módulos

A mesa liga e desliga cada um antes de começar. Uma carta é um par
**(lugar, pergunta)**, então o mesmo país pode voltar com outra pergunta.

| Módulo | A carta mostra | Você responde |
|---|---|---|
| **Bandeira → país** | a bandeira | o país |
| **País → capital** | o nome do país | a capital |
| **Capital → país** | o nome da capital | o país |

Com os três ligados e o mundo todo no baralho são **712 cartas** possíveis.

## A partida

| | |
|---|---|
| acertar sem dica | **3** |
| acertar com uma dica | **2** |
| acertar com duas dicas | **1** |
| errar ou passar | **0** |

As dicas mudam com o módulo, porque dica boa num é entrega no outro — mostrar a
capital quando a pergunta *é* a capital acabaria com a carta:

- **Bandeira → país:** continente, depois capital.
- **País → capital:** continente, depois a inicial e o número de letras.
- **Capital → país:** continente, depois **a bandeira** aparece.

Nenhuma dica é inventada: tudo sai do que a fonte trouxe, e o que não veio
simplesmente não vira dica.

**Sozinho vale.** Sem ninguém cadastrado a partida começa como "Você" e a tela
de passar o celular some.

O celular lembra o que já saiu, e lembra **por módulo** — o Peru pode voltar
como capital depois de já ter saído como bandeira. A memória fica no navegador
de quem segura o aparelho e é apagada sozinha quando o banco é regerado.

## O que a mesa escolhe

**Módulos**, **quantas cartas para cada um**, **de onde saem** (mundo todo ou um
continente), **quem entra** (só os 195 países, ou com os territórios) e a
**régua**.

A régua merece explicação, e a tela do jogo dá ela por extenso: "a metade mais
lida" é a metade do recorte cujo artigo foi mais lido **na Wikipédia em
português** nos últimos 12 meses. Mede o quanto o mundo lusófono olha pra
aquele lugar — não o quanto a pergunta é difícil. Por isso Cabo Verde aparece
à frente da França: é país de língua portuguesa, e quem lê Wikipédia em
português lê sobre ele. A régua serve pra tirar Tokelau e Ilha Norfolk da mesa,
não pra dizer que a França é difícil.

## O baralho

**240 lugares: 195 países e 45 territórios.** O universo é a **ISO 3166-1
alpha-2**, a lista de códigos de duas letras que o mundo usa pra identificar
lugar. Os 195 são os 193 da ONU mais o Vaticano e a Palestina, que são
observadores — lista fechada, ninguém aqui decidindo o que é país.

| Fonte | O que vem de lá |
|---|---|
| Wikidata (SPARQL) | quem tem código ISO, nome em português, apelidos, capital, continente, população, data de adoção da bandeira |
| Wikimedia Commons | a imagem — PNG renderizado do SVG oficial, o mesmo arquivo que a Wikipédia usa |
| Wikipédia lusófona | as notas: o parágrafo sobre a bandeira (237 cartas) e sobre a cidade (236), com link |
| Pageviews API | quanto o artigo do lugar foi lido em português nos últimos 12 meses — é a régua de "mais fácil" |

As 240 bandeiras ficam em `img/`, dentro do repositório, e somam 1,5 MB depois
do `pngquant`. É de propósito: o jogo não depende de CDN nenhum pra rodar.

## As capitais

**237 dos 240 lugares têm capital.** Ficam sem Hong Kong e Tokelau (o Wikidata
não dá capital pra nenhum dos dois) — eles simplesmente não viram carta nos
módulos de capital.

Três decisões fizeram esse dado sair certo, e cada uma consertou um erro real:

**Ler por identificador, não por nome.** "Bamaco" e "Bamako" são dois rótulos da
mesma cidade. Agrupando por texto, o Mali parecia ter duas capitais. Agrupando
por Q-id, é uma cidade com dois nomes — e o nome extra vira apelido aceito no
autocomplete, junto com Moscovo, Banguecoque e Tasquente.

**Jogar fora capital de antigamente.** Lagos foi capital da Nigéria até 1991 e
continua no item do Wikidata, com data de término. Sem olhar essa data, a
Nigéria vinha com duas capitais — ou, do jeito que estava antes, com nenhuma.

**Rank preferencial ordena, não exclui.** Essa foi a correção mais sutil. O
Wikidata marca Amsterdã e Jerusalém como preferenciais; usar isso pra descartar
o resto teria feito o jogo dizer que **Haia** e **Tel Aviv** estão erradas. O
rank decide qual capital a carta lê primeiro; o que sai mesmo é o que tem data
de término.

### Onze lugares com mais de uma capital

Não é grafia diferente — são cidades diferentes, e **todas valem o ponto**. A
carta abre explicando por que são várias: África do Sul (três, uma por poder),
Bolívia, Países Baixos, Malásia, Sri Lanka, Essuatíni, Iêmen, Benim, Paquistão,
Montserrat, Palestina e as Ilhas Geórgia do Sul.

Essas explicações estão escritas à mão em `CAPITAIS_MULTIPLAS`, no
`gerador.py`, porque a informação que faz a carta valer alguma coisa **não está
na fonte**: o Wikidata guarda as três capitais da África do Sul sem dizer qual
poder fica em qual.

### Sete quase-acertos que contam

Cidade que não é a capital oficial mas é onde o governo senta de verdade: Haia,
Tel Aviv, Jerusalém (para a Palestina), Abidjã, Dar es Salaam, Bujumbura e
Valparaíso. Quem responde isso **não errou**, e marcar como erro seria o jogo
mentindo — a mesma regra das bandeiras gêmeas. Vale o ponto cheio, e a carta
diz o fato que torna a resposta aceitável.

O Wikidata não serve pra montar essa lista: ele **deprecia** Haia e Tel Aviv, ou
seja, marca como erradas, e nem lista Abidjã. Por isso ela é escrita à mão em
`QUASE`, com o motivo de cada linha.

### Uma capital que serve a dois lugares

**Kingston** é a capital da Jamaica e a da Ilha Norfolk. No módulo *capital →
país* ela ficaria com duas respostas certas por um motivo que não é geografia,
então esse par não vira carta. Nos outros módulos as duas seguem normalmente.

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
explicando por quê.

## Onde a fonte precisou de remendo

Sete lugares no `gerador.py` têm dado escrito à mão. Todos estão comentados no
código, e todos existem porque a fonte tem buraco — nenhum é opinião nossa:

- **`EXCECOES`** — a cadeira da Dinamarca na ONU está no item *Reino da
  Dinamarca*, que não tem código ISO; o código está em *Dinamarca*. Sem essa
  linha o baralho teria 194 países. O Kosovo está aqui pelo motivo de cima.
- **`CORRECOES`** — o Wikidata escreve "Groelândia" com erro de digitação, e usa
  o nome longo de tratado onde a mesa fala o curto ("Reino dos Países Baixos",
  "República Popular da China").
- **`CORRECOES_CIDADE`** — "Cidade de Bruxelas" é o município, não o nome que se
  fala; e o rótulo em português de Mbabane vem "Mebabane". A chave é o Q-id,
  porque rótulo muda; o nome antigo continua valendo como apelido.
- **`APELIDOS`** — "holanda", "eua", "kiribati", "bahrein": o que alguém digita
  de verdade no celular e o `altLabel` não tem.
- **`CAPITAIS_MULTIPLAS`**, **`QUASE`**, **`VETADOS`** e **`GEMEAS`** — as
  quatro listas explicadas nas seções acima.

O gerador **confere as listas escritas à mão contra a fonte** a cada rodada: se
uma capital que está no `CAPITAIS_MULTIPLAS` sumir do Wikidata, ou se aparecer
um lugar com duas capitais sem explicação escrita, ele imprime o aviso em vez de
fingir que está tudo certo.

**A proporção da bandeira ficou de fora da carta.** O Wikidata mistura as
convenções entre um item e outro: a Romênia aparece como "2:3" e o Chade como
"3:2" para bandeiras do mesmo formato. Número que não dá pra afirmar direito não
vai pra carta. Onde a proporção importa mesmo — nas gêmeas — ela está escrita à
mão, conferida na especificação oficial de cada uma.

## No celular

A caixa de sugestões tem **altura fixa e fica sempre na tela**, mesmo vazia.
Antes ela crescia e encolhia a cada letra digitada — com o teclado do celular
aberto, a página inteira refluía embaixo e a tela pulava. Espaço reservado custa
dois dedos de altura e paga com o silêncio: digitando, nada se move. Pelo mesmo
motivo o botão de dica não rouba o foco do campo, o alvo da carta (bandeira ou
pergunta) tem a mesma altura nos três módulos, e ele encolhe em tela baixa pra
rodada caber sem rolagem.

## Regerar o banco

```bash
cd geografia
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
lista o jogo, que os três módulos caem, que o autocomplete acha lugar e cidade
por duas letras e que o console fica limpo.
