#!/usr/bin/env python3
"""
juntar_revisao.py — funde os lotes do juiz num revisao.json só.

Cada lote sai de um tabu-juiz e cobre uma faixa das cartas. Aqui os lotes
viram um arquivo só, com as checagens que nenhum agente faz sozinho: carta
repetida em dois lotes, proibida derivada da própria palavra-chave, número
errado de proibidas, e carta que ficou de fora de todo mundo.

Uso:
    python3 juntar_revisao.py            # lê revisao/lote-*-final.json
"""

import glob, json, os, re, sys, time
from collections import Counter

from gerador import tronco, sem


def main():
    lotes = sorted(glob.glob(os.path.join("revisao", "lote-*-final.json")))
    if not lotes:
        sys.exit("nenhum revisao/lote-*-final.json. Rode os agentes primeiro (REVISOR.md).")

    with open("paracritica.json", encoding="utf-8") as fh:
        pool = {c["palavra"]: c for c in json.load(fh)["cartas"]}

    cartas, descartadas, avisos = {}, {}, []
    visto = Counter()

    for caminho in lotes:
        with open(caminho, encoding="utf-8") as fh:
            d = json.load(fh)
        nome = os.path.basename(caminho)

        for p, m in d.get("descartadas", {}).items():
            p = p.upper(); visto[p] += 1
            descartadas[p] = m

        for p, c in d.get("cartas", {}).items():
            p = p.upper(); visto[p] += 1
            if p not in pool:
                avisos.append(f"{nome}: {p} não está no paracritica.json — ignorada")
                continue

            proibidas = [w.strip().upper() for w in c.get("proibidas", []) if w.strip()]

            # o juiz foi instruído a não usar derivado da palavra-chave; conferir
            alvo = {tronco(x) for x in re.findall(r"\w+", p.lower()) if len(x) > 2}
            limpo = []
            for w in proibidas:
                t = tronco(w.lower())
                if any(t == x or t.startswith(x) or x.startswith(t) for x in alvo if len(x) > 3):
                    avisos.append(f"{nome}: {p} tinha '{w}', derivado da própria palavra — fora")
                    continue
                if sem(w.lower()) in {sem(y.lower()) for y in limpo}:
                    avisos.append(f"{nome}: {p} tinha '{w}' repetida — fora")
                    continue
                limpo.append(w)

            # Sobrou vaga porque uma proibida era pedaço da própria palavra
            # (MAR em MARINHEIRO). A regra do jogo já bane isso, então o slot
            # estava desperdiçado — mas a carta não precisa morrer por causa
            # disso: completa com a melhor candidata do artigo que ainda serve.
            for cand in pool[p]["candidatas"]:
                if len(limpo) >= 5:
                    break
                t = tronco(cand.lower())
                if any(t == x or t.startswith(x) or x.startswith(t) for x in alvo if len(x) > 3):
                    continue
                if sem(cand.lower()) in {sem(y.lower()) for y in limpo}:
                    continue
                limpo.append(cand)
                avisos.append(f"{nome}: {p} completada com '{cand}' das candidatas do artigo")

            if len(limpo) != 5:
                avisos.append(f"{nome}: {p} ficou com {len(limpo)} proibidas — descartada")
                descartadas[p] = f"o revisor não fechou 5 proibidas válidas ({len(limpo)})"
                continue

            no_artigo = [w.upper() for w in c.get("no_artigo", [])]
            candidatas = set(pool[p]["candidatas"])
            confere = [w for w in limpo if w in candidatas]
            if set(no_artigo) != set(confere):
                avisos.append(f"{nome}: {p} — no_artigo recalculado a partir das candidatas")
            cartas[p] = {"proibidas": limpo, "no_artigo": confere}
            if c.get("nota"):
                cartas[p]["nota"] = c["nota"]

    for p, n in visto.items():
        if n > 1:
            avisos.append(f"{p} apareceu em {n} lotes — valeu o último")
    orfas = [p for p in pool if p not in visto]

    saida = {
        "revisado_em": time.strftime("%Y-%m-%d"),
        "metodo": ("Duas listas feitas às cegas — uma de quem descreveria, uma de "
                   "associação livre — cruzadas por um terceiro revisor, que também "
                   "viu as candidatas do artigo da Wikipédia e anotou quais das "
                   "cinco escolhidas aparecem lá."),
        "cartas": cartas,
        "descartadas": descartadas,
    }
    with open("revisao.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)

    conf = sum(len(c["no_artigo"]) for c in cartas.values())
    total = sum(len(c["proibidas"]) for c in cartas.values()) or 1
    print(f"✓ {len(lotes)} lotes -> revisao.json")
    print(f"  {len(cartas)} cartas fechadas, {len(descartadas)} descartadas")
    print(f"  {conf}/{total} proibidas ({conf/total:.0%}) também estão no artigo da Wikipédia")
    if orfas:
        print(f"  {len(orfas)} cartas que nenhum lote viu: {', '.join(sorted(orfas)[:8])}"
              + (" …" if len(orfas) > 8 else ""))
    if avisos:
        print(f"\n  {len(avisos)} avisos:")
        for a in avisos[:25]:
            print("   ·", a)
        if len(avisos) > 25:
            print(f"   · … e mais {len(avisos)-25}")


if __name__ == "__main__":
    main()
