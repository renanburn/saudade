#!/usr/bin/env python3
"""Avalia o detector de contradição contra o dataset anotado (dataset/pares.jsonl).

Mede o FILTRO determinístico (pares_candidatos + forca_marca), que é a parte
barata e sempre ligada. O juiz LLM é opcional e avaliado à parte (--juiz).

Verdade usada: rotulo_humano quando existir; senão rotulo_maquina, e o
relatório deixa claro qual régua está em uso (pré-anotação não é benchmark,
é fumaça de teto; o número que vale sai depois da anotação humana cega).

Uso:
    python3 testes/avaliar.py
    python3 testes/avaliar.py --dataset dataset/pares.jsonl --juiz sonnet
"""
import argparse
import importlib.machinery
import importlib.util
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent.parent
CLI = AQUI / "bin" / "saudade"

loader = importlib.machinery.SourceFileLoader("saudade_cli", str(CLI))
spec = importlib.util.spec_from_loader("saudade_cli", loader)
sd = importlib.util.module_from_spec(spec)
sys.modules["saudade_cli"] = sd
loader.exec_module(sd)


def carrega(caminho):
    pares = []
    with open(caminho) as f:
        for i, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            p = json.loads(linha)
            p["_n"] = i
            pares.append(p)
    return pares


def rotulo_de(p):
    return p.get("rotulo_humano") or p.get("rotulo_maquina")


def detecta_par(p):
    """O filtro acha este par? Reconstrói o cenário mínimo: dois fatos, mesma
    entity (ou entity citada), o novo mais recente, e roda pares_candidatos."""
    antigo = {"id": 1, "entity": p["antigo"]["entity"], "tipo": p["antigo"]["tipo"],
              "ts": p["antigo"]["ts"], "texto": p["antigo"]["texto"]}
    novo = {"id": 2, "entity": p["novo"]["entity"], "tipo": p["novo"]["tipo"],
            "ts": p["novo"]["ts"], "texto": p["novo"]["texto"]}
    cand = sd.pares_candidatos([antigo, novo], dias=36500, max_pares=10)
    return any(an["id"] == 1 and nv["id"] == 2 for _s, an, nv in cand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(AQUI / "dataset" / "pares.jsonl"))
    ap.add_argument("--verboso", action="store_true")
    a = ap.parse_args()

    pares = carrega(a.dataset)
    humanos = sum(1 for p in pares if p.get("rotulo_humano"))
    regua = "HUMANA" if humanos == len(pares) else ("mista" if humanos else "máquina (pré-anotação)")
    print(f"dataset: {len(pares)} pares · régua: {regua} ({humanos} anotados por humano)")
    if humanos < len(pares):
        print("AVISO: sem anotação humana completa isto é fumaça de teto, não benchmark.\n")

    # O filtro deve ACHAR contradiz e parcial (recall) e idealmente pular nao_contradiz
    # (precisão do funil; a precisão final é papel do juiz + humano).
    tp = fn = fp = tn = 0
    erros = []
    for p in pares:
        verdade = rotulo_de(p)
        achou = detecta_par(p)
        positivo = verdade in ("contradiz", "parcial")
        if positivo and achou:
            tp += 1
        elif positivo and not achou:
            fn += 1
            erros.append(("PERDEU", p))
        elif not positivo and achou:
            fp += 1
            erros.append(("PEGOU À TOA", p))
        else:
            tn += 1

    recall = tp / (tp + fn) if tp + fn else 0.0
    precisao = tp / (tp + fp) if tp + fp else 0.0
    print(f"filtro determinístico (funil pro juiz):")
    print(f"  recall    {recall:.2f}  ({tp}/{tp + fn} contradições chegam ao juiz)")
    print(f"  precisão  {precisao:.2f}  ({tp}/{tp + fp} do que chega é contradição de verdade)")
    print(f"  matriz: TP={tp} FN={fn} FP={fp} TN={tn}")
    print(f"\n  O número que NÃO pode cair é o recall: FN é contradição que ninguém verá.")
    print(f"  FP custa só tempo de juiz/humano; FN custa decisão tomada sobre fato morto.")

    if a.verboso and erros:
        print("\nerros:")
        for tipo, p in erros[:20]:
            print(f"  [{tipo}] {p['id']} ({rotulo_de(p)}): '{p['antigo']['texto'][:60]}' vs '{p['novo']['texto'][:60]}'")

    # gate honesto pra CI: recall do funil não pode regredir abaixo de 0.8
    if tp + fn > 0 and recall < 0.8:
        print(f"\nFALHA: recall {recall:.2f} < 0.80")
        sys.exit(1)
    print("\nok")


if __name__ == "__main__":
    main()
