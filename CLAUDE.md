# Jogos da Turma — como mexer neste repositório

Coleção de jogos de mesa pra jogar com amigos pelo celular. Site estático, sem
backend, no ar em **https://leoborja.github.io/jogos-da-turma/** (GitHub Pages,
branch `main`, pasta raiz).

## Estrutura

```
index.html            a base: lista os jogos. NÃO é de nenhum jogo.
comum.css             o visual que todos os jogos dividem
logo.svg              a marca; icone.svg + icone-*.png são o ícone de app
manifest.webmanifest  deixa a base virar app na tela de início do celular
jogos.json            índice gerado — não edite à mão
atualizar_jogos.py    gera o jogos.json varrendo */jogo.json
top10/                um jogo, autocontido
  jogo.json           a ficha que a base lê
  index.html          o jogo
  ...                 tudo mais que ele precisa
```

## Regra de ouro: cada jogo mora na sua pasta

Costuma ter mais de uma pessoa (ou mais de uma sessão do Claude) escrevendo
jogo diferente ao mesmo tempo. Então:

**Pode mexer à vontade:** qualquer arquivo dentro da pasta do SEU jogo.

**Não mexa:** `comum.css`, o `index.html` da raiz, o `atualizar_jogos.py`,
`logo.svg`, `icone*.png`, `manifest.webmanifest`, e a pasta de qualquer outro
jogo. O jogo pode ter ícone próprio — coloque na pasta dele. Se o seu jogo precisa de um estilo que o
`comum.css` não tem, escreva no `<style>` do próprio jogo — duplicar um pouco
de CSS custa menos que dois jogos brigando pelo mesmo arquivo.

**`jogos.json` é gerado.** Se der conflito de merge nele, não resolva na mão:
rode `python3 atualizar_jogos.py` de novo.

## Criar um jogo novo

1. `mkdir <slug>` — slug curto, minúsculo, sem acento (`top10`, `mimica`).
2. `<slug>/jogo.json`:

```json
{
  "slug": "mimica",
  "nome": "Mímica",
  "tagline": "Uma frase dizendo do que se trata.",
  "descricao": "Um parágrafo curto: como joga e de onde vem o conteúdo.",
  "emoji": "🎭",
  "cor": "verde",
  "jogadores": "4 a 12",
  "duracao": "30 min",
  "precisa": "um celular na mesa",
  "status": "construindo"
}
```

`slug` tem que ser igual ao nome da pasta. `cor` é uma das do `comum.css`:
`amarelo`, `coral`, `laranja`, `verde`, `rosa`, `lilas` — escolha uma que
outro jogo ainda não usou. `status` é `ideia`, `construindo` ou `pronto`;
só `pronto` fica clicável na base, e só passa na validação se existir
`<slug>/index.html`.

3. `<slug>/index.html` começando assim:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gabarito:wght@600;800;900&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../comum.css">
<style>/* só o que for deste jogo */</style>
```

Envolva a página em `<div id="app">` e ponha um link de volta pra base:
`<a class="botao mini" href="../">‹ Outros jogos</a>`.

4. `python3 atualizar_jogos.py` — valida a ficha e regenera o índice.

## O visual

Neobrutalismo: contorno preto de 3px, sombra dura sem blur, cor chapada, botão
que afunda na própria sombra quando é apertado. Display **Gabarito 900**,
interface **Space Grotesk**. Fundo claro com bolinhas.

O `comum.css` já entrega `.carta`/`.faixa`/`.corpo`, `.bloco`, `.rotulo`,
`button` (com `.principal`, `.mini`, `.perigo`, `.on`), `input`, `.aviso`
(`.certo`/`.errado`/`.duvida`), `details`/`summary` e as variáveis de cor.
Use isso antes de inventar.

Cor sólida forte é escassa de propósito: reserve o amarelo cheio pro botão
que faz a rodada andar. Se tudo for colorido, nada se destaca.

## Conteúdo: a regra que não se negocia

O jogo é jogado por gente que confia no que está na tela. Então:

- **Dado tem que ser verdadeiro e conferível.** Prefira gerar de base aberta a
  escrever à mão. Se escrever à mão, cite a fonte.
- **Toda carta explica o que ela afirma.** No Top 10 cada carta traz uma nota
  dizendo o que o número mede e o que fica de fora do cálculo — é isso que
  encerra a discussão na mesa. Faça o equivalente no seu jogo.
- **Número estranho não se esconde, se explica.** Se Singapura aparece com
  258% de energia importada, a saída é contar por que, não tirar a carta.

## Antes de subir

Sirva a pasta raiz por HTTP (não abra o arquivo direto — `fetch` não funciona
em `file://`) e teste a base e o jogo:

```bash
python3 -m http.server 8090     # se a 8090 estiver ocupada, escolha outra
```

Confira: a base lista o jogo, o link abre, o jogo roda, o botão volta, e o
console não tem erro.
