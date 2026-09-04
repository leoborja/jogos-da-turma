#!/usr/bin/env python3
"""
Monta o jogos.json que a base lê, varrendo */jogo.json.

Um site estático não consegue listar pasta sozinho, então esse arquivo é o
índice. Rode depois de criar ou mexer no jogo.json de qualquer jogo:

    python3 atualizar_jogos.py

Como jogos.json é gerado, se der conflito de merge com outro branch é só
rodar de novo — não resolva na mão.
"""

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).parent
OBRIGATORIOS = ["slug", "nome", "tagline", "emoji", "cor", "jogadores", "status"]
CORES = {"amarelo", "coral", "azul", "verde", "laranja", "lilas"}
STATUS = {"pronto", "construindo", "ideia"}


def main():
    jogos, erros = [], []
    for ficha in sorted(RAIZ.glob("*/jogo.json")):
        pasta = ficha.parent.name
        try:
            j = json.loads(ficha.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            erros.append(f"{ficha}: JSON inválido ({e})")
            continue

        faltam = [c for c in OBRIGATORIOS if not j.get(c)]
        if faltam:
            erros.append(f"{ficha}: faltam os campos {', '.join(faltam)}")
            continue
        if j["slug"] != pasta:
            erros.append(f"{ficha}: slug '{j['slug']}' não bate com a pasta '{pasta}'")
            continue
        if j["cor"] not in CORES:
            erros.append(f"{ficha}: cor '{j['cor']}' não existe (use {', '.join(sorted(CORES))})")
            continue
        if j["status"] not in STATUS:
            erros.append(f"{ficha}: status '{j['status']}' não existe (use {', '.join(sorted(STATUS))})")
            continue
        if j["status"] == "pronto" and not (ficha.parent / "index.html").exists():
            erros.append(f"{ficha}: está 'pronto' mas não tem index.html na pasta")
            continue
        jogos.append(j)

    # jogo pronto primeiro; dentro do mesmo status, ordem alfabética
    ordem = {"pronto": 0, "construindo": 1, "ideia": 2}
    jogos.sort(key=lambda j: (ordem[j["status"]], j["nome"].lower()))

    (RAIZ / "jogos.json").write_text(
        json.dumps({"jogos": jogos}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    for j in jogos:
        print(f"  {j['emoji']}  {j['nome']:<22} {j['status']:<12} /{j['slug']}/")
    print(f"\n{len(jogos)} jogo(s) -> jogos.json")
    if erros:
        print("\nproblemas:")
        for e in erros:
            print("  -", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
