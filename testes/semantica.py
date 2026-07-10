#!/usr/bin/env python3
"""Testes da semântica da saudade. Roda sem pytest: python3 testes/semantica.py

Cobre o que NÃO pode regredir:
  1. a cadeia pendência → baixa → baixa superada (REABRE) → pendência superada
  2. a regra da sequência líder (#id no meio do texto não conta)
  3. o lint de dois-fatos-numa-linha
  4. round-trip real num banco temporário: init, add, supersede, buscar --vigente,
     reafirmar aresta invalidada (o índice único parcial em ação)
"""
import importlib.machinery
import importlib.util
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent.parent
CLI = AQUI / "bin" / "saudade"

# importa o CLI como módulo (arquivo sem .py)
loader = importlib.machinery.SourceFileLoader("saudade_cli", str(CLI))
spec = importlib.util.spec_from_loader("saudade_cli", loader)
sd = importlib.util.module_from_spec(spec)
sys.modules["saudade_cli"] = sd
loader.exec_module(sd)

FALHAS = []


def check(nome, got, want):
    ok = got == want
    print(f"  {'ok   ' if ok else 'FALHA'} {nome}: got={got!r} want={want!r}")
    if not ok:
        FALHAS.append(nome)


def fato(id_, tipo, texto):
    return {"id": id_, "entity": "E", "tipo": tipo, "ts": "2026-01-01 10:00", "texto": texto}


print("\n== 1. estado derivado por evento ==")
CENAS = {
    "só a pendência": ([fato(10, "pendencia", "fazer X")], set()),
    "com baixa": ([fato(10, "pendencia", "fazer X"),
                   fato(11, "resolvido", "#10 · feito")], {10}),
    "baixa superada REABRE": ([fato(10, "pendencia", "fazer X"),
                               fato(11, "resolvido", "#10 · feito"),
                               fato(12, "supersede", "#11 · a baixa estava errada")], {11}),
    "pendência superada morre": ([fato(10, "pendencia", "fazer X"),
                                  fato(11, "resolvido", "#10 · feito"),
                                  fato(12, "supersede", "#11 · baixa errada"),
                                  fato(13, "supersede", "#10 · a tarefa não faz mais sentido")], {10, 11}),
}
for nome, (fatos, want) in CENAS.items():
    mortos = sd.superseded_ids(fatos)
    baixas = sd.resolved_ids(fatos, mortos)
    check(nome, mortos | baixas, want)

print("\n== 2. sequência líder (regra do #id) ==")
check("id líder conta", sd.leading_ids("#12 · motivo"), [12])
check("dois ids líderes", sd.leading_ids("#12, #13 · motivo"), [12, 13])
check("id no meio NÃO conta", sd.leading_ids("motivo citando #12 no meio"), [])
check("sem id", sd.leading_ids("só texto"), [])

print("\n== 3. lint ==")
e, w = sd.lint_texto("supersede", "sem id nenhum")
check("supersede sem alvo é erro", len(e) > 0, True)
e, w = sd.lint_texto("decisao", "o orçamento foi aprovado; e decidiu trocar de fornecedor")
check("dois fatos numa linha avisa", any("DOIS fatos" in x or "3+" in x for x in w), True)
e, w = sd.lint_texto("decisao", "mantém o preço da proposta em 7.350")
check("fato limpo passa", (e, w), ([], []))
e, w = sd.lint_texto("observacao", "resolvido junto com #99 ontem")
check("menção a #id sem ser evento avisa", len(w) > 0, True)

print("\n== 4. marcas de reversão ==")
check("decidiu ficar é forte", sd.forca_marca("o cliente decidiu ficar com o plano antigo"), 2)
check("acento não quebra", sd.forca_marca("voltou atrás na decisão"), 2)
check("correção é fraca", sd.forca_marca("correção do valor da nota"), 1)
check("rotina não dispara", sd.forca_marca("bug corrigido no deploy de ontem"), 0)

print("\n== 5. round-trip num banco temporário ==")
tmp = tempfile.mkdtemp(prefix="saudade-test-")
db = os.path.join(tmp, "m.db")
env = dict(os.environ, SAUDADE_DB=db)


def cli(*args, esperado=0):
    r = subprocess.run([sys.executable, str(CLI), *args], env=env, capture_output=True, text=True)
    if r.returncode != esperado:
        print(f"  FALHA cli{args}: exit={r.returncode}\n{r.stderr}")
        FALHAS.append(str(args))
    return r


cli("init")
cli("add", "Projeto X", "decisao", "vamos de SQLite puro")
cli("add", "Projeto X", "pendencia", "escrever o README")
cli("add", "Projeto X", "supersede", "#1 · mudamos pra arquivo texto", "--at", "2026-01-02 10:00")
r = cli("buscar", "SQLite")
check("busca acha e marca superado", "SUPERADO" in r.stdout, True)
r = cli("buscar", "SQLite", "--vigente")
check("--vigente esconde o morto", "#1 " not in r.stdout, True)
r = cli("add", "projeto x", "observacao", "variação de caixa", esperado=4)
check("variação canônica de entity é bloqueada", r.returncode, 4)
r = cli("add", "Projeto X", "supersede", "#999 · alvo fantasma", esperado=3)
check("supersede de id inexistente é bloqueado", r.returncode, 3)

cli("add", "Ferramenta Y", "observacao", "nasceu")
cli("rel", "add", "Ferramenta Y", "Projeto X", "pertence a")
cli("rel", "invalidate", "1", "--reason", "saiu do projeto")
r = cli("rel", "add", "Ferramenta Y", "Projeto X", "pertence a")
check("aresta morta pode ser reafirmada", "+" in r.stdout and "#2" in r.stdout, True)
r = cli("rel", "add", "Ferramenta Y", "Projeto X", "pertence a")
check("duplicata VIVA é recusada", "já existe" in r.stdout, True)

con = sqlite3.connect(db)
tot = con.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
con.close()
check("nada foi apagado (2 arestas no banco)", tot, 2)
shutil.rmtree(tmp)

print()
if FALHAS:
    print(f"FALHOU: {len(FALHAS)} checagem(ns): {FALHAS}")
    sys.exit(1)
print(f"todas as checagens passaram")
