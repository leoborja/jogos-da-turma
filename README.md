# Jogos da Turma

Jogos de mesa pra jogar com os amigos, direto do celular. Site estático, sem
baixar nada, sem cadastro.

**→ https://jogosdaturma.com.br/**

## Os jogos

| | Jogo | O que é | Status |
|---|---|---|---|
| 🔟 | **[Top 10](top10/)** | A carta pergunta, a resposta é um ranking de dez. Vocês vão falando sem repetir e sem errar. 249 cartas de países e línguas. | pronto |
| 🏁 | **[Bandeiras](bandeiras/)** | A bandeira aparece, você digita o país. O celular passa de mão em mão e a carta abre explicando a bandeira. 240 cartas: 195 países e 45 territórios. Dá pra jogar sozinho. | pronto |

## Como isso é montado

Cada jogo mora na própria pasta e é autocontido; a raiz tem só a base que os
lista, o CSS que todos dividem e o script que gera o índice.

```
index.html            a base
comum.css             o visual comum
logo.svg              a marca (a turma espiando por cima de uma carta)
icone.svg             a mesma marca em cima de um quadrado amarelo
icone-180.png         ícone de app (iOS)
icone-512.png         ícone de app (Android)
manifest.webmanifest  deixa a base virar app na tela de início
jogos.json            índice gerado por atualizar_jogos.py
top10/                um jogo
```

A marca é SVG desenhado à mão, no mesmo traço do site: contorno preto grosso e
cor chapada. A interrogação da carta é traço, não texto — assim ela sai igual
em qualquer sistema, inclusive como favicon.

Pra rodar local, sirva a raiz por HTTP (`fetch` não funciona em `file://`):

```bash
python3 -m http.server 8090
```

Pra criar um jogo novo, o passo a passo está no [CLAUDE.md](CLAUDE.md).
