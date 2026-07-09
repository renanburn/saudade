import json
import sys
from collections import Counter, defaultdict

PATH = "/Users/palastudio/.claude/jobs/ce93c9a0/tmp/dataset-saudade/pares.jsonl"

erros = []
avisos = []

with open(PATH, encoding="utf-8") as f:
    linhas = [l for l in f.read().splitlines() if l.strip()]

# 1. 72 linhas
if len(linhas) != 72:
    erros.append(f"Esperado 72 linhas, encontrado {len(linhas)}")
else:
    print(f"OK: 72 linhas encontradas")

# 2. JSON valido em todas
registros = []
for i, l in enumerate(linhas, 1):
    try:
        registros.append(json.loads(l))
    except json.JSONDecodeError as e:
        erros.append(f"Linha {i}: JSON invalido - {e}")

if len(registros) == len(linhas):
    print(f"OK: JSON valido em todas as {len(registros)} linhas")

# 3. ids unicos e sequenciais
ids = [r["id"] for r in registros]
esperado = [f"par-{i:03d}" for i in range(1, len(registros) + 1)]
if ids == esperado:
    print("OK: ids unicos e sequenciais (par-001 .. par-072)")
else:
    erros.append(f"ids fora de sequencia. Esperado {esperado[:3]}...{esperado[-3:]}, obtido {ids[:3]}...{ids[-3:]}")
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        erros.append(f"ids duplicados: {dup}")

# 4. rotulo_humano sempre null
nao_null = [r["id"] for r in registros if r.get("rotulo_humano") is not None]
if nao_null:
    erros.append(f"rotulo_humano nao-nulo em: {nao_null}")
else:
    print("OK: rotulo_humano é null em todos os 72 registros")

# 5. distribuicao de rotulos
dist_rotulo = Counter(r["rotulo_maquina"] for r in registros)
print(f"\nDistribuicao rotulo_maquina: {dict(dist_rotulo)}")
esperado_min = {"contradiz": 24, "nao_contradiz": 24, "parcial": 12}
for rot, minimo in esperado_min.items():
    if dist_rotulo.get(rot, 0) < minimo:
        erros.append(f"rotulo '{rot}' tem {dist_rotulo.get(rot,0)}, esperado >= {minimo}")
total_dist = sum(dist_rotulo.values())
if total_dist != 72:
    erros.append(f"soma da distribuicao de rotulos != 72 (deu {total_dist})")

rotulos_validos = {"contradiz", "nao_contradiz", "parcial"}
invalidos = [r["id"] for r in registros if r["rotulo_maquina"] not in rotulos_validos]
if invalidos:
    erros.append(f"rotulo_maquina invalido em: {invalidos}")

# 6. distribuicao por dominio
dist_dominio = Counter(r["dominio"] for r in registros)
print(f"Distribuicao dominio: {dict(dist_dominio)}")

# cruzamento rotulo x dominio
cruz = defaultdict(Counter)
for r in registros:
    cruz[r["dominio"]][r["rotulo_maquina"]] += 1
print("\nCruzamento dominio x rotulo:")
for dom in sorted(cruz):
    print(f"  {dom}: {dict(cruz[dom])}")

# 7. nenhum texto duplicado (considerando antigo.texto e novo.texto juntos)
textos = []
for r in registros:
    textos.append(r["antigo"]["texto"])
    textos.append(r["novo"]["texto"])
dup_textos = [t for t, c in Counter(textos).items() if c > 1]
if dup_textos:
    erros.append(f"textos duplicados encontrados ({len(dup_textos)}): {dup_textos[:5]}")
else:
    print(f"OK: nenhum texto duplicado entre os {len(textos)} textos (antigo+novo)")

# 8. estrutura de campos obrigatoria
campos_obrig = {"id", "dominio", "antigo", "novo", "rotulo_maquina", "rotulo_humano", "notas"}
for r in registros:
    faltando = campos_obrig - set(r.keys())
    if faltando:
        erros.append(f"{r.get('id','?')}: campos faltando {faltando}")
    for lado in ("antigo", "novo"):
        sub = r.get(lado, {})
        sub_campos = {"ts", "entity", "tipo", "texto"}
        faltando_sub = sub_campos - set(sub.keys())
        if faltando_sub:
            erros.append(f"{r.get('id','?')}.{lado}: campos faltando {faltando_sub}")

# 9. vocabulario diferente em pelo menos 8 contradiz (heuristica: <40% palavras em comum)
def palavras(txt):
    return set(w.strip(".,;:!?()").lower() for w in txt.split() if len(w) > 3)

contradiz_vocab_diff = 0
for r in registros:
    if r["rotulo_maquina"] == "contradiz":
        pa, pn = palavras(r["antigo"]["texto"]), palavras(r["novo"]["texto"])
        if pa and pn:
            jaccard = len(pa & pn) / len(pa | pn)
            if jaccard < 0.15:
                contradiz_vocab_diff += 1
print(f"\nPares 'contradiz' com vocabulario bem distinto (heuristica jaccard<0.15): {contradiz_vocab_diff} (minimo pedido: 8)")
if contradiz_vocab_diff < 8:
    avisos.append(f"Apenas {contradiz_vocab_diff} pares contradiz com vocabulario bem distinto pela heuristica (minimo 8) - checar manualmente, heuristica e conservadora")

print("\n" + "=" * 50)
if erros:
    print(f"FALHOU: {len(erros)} erro(s)")
    for e in erros:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("VALIDACAO OK: todos os checks passaram")
if avisos:
    print(f"\nAvisos ({len(avisos)}):")
    for a in avisos:
        print(f"  - {a}")
