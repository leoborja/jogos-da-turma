# Jogos da Turma

Jogos de mesa pra jogar com os amigos, direto do celular. Site estático, sem
baixar nada, sem cadastro.

**→ https://leoborja.github.io/jogos-da-turma/**

## Os jogos

| | Jogo | O que é | Status |
|---|---|---|---|
| 🔟 | **[Top 10](top10/)** | A carta pergunta, a resposta é um ranking de dez. Vocês vão falando sem repetir e sem errar. 249 cartas de países e línguas. | pronto |

## Como isso é montado

Cada jogo mora na própria pasta e é autocontido; a raiz tem só a base que os
lista, o CSS que todos dividem e o script que gera o índice.

```
index.html            a base
comum.css             o visual comum
jogos.json            índice gerado por atualizar_jogos.py
top10/                um jogo
```

Pra rodar local, sirva a raiz por HTTP (`fetch` não funciona em `file://`):

```bash
python3 -m http.server 8090
```

Pra criar um jogo novo, o passo a passo está no [CLAUDE.md](CLAUDE.md).
