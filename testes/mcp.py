#!/usr/bin/env python3
"""Teste do servidor MCP: handshake, tools/list e um ciclo real add → estado → buscar.

Sobe o servidor como subprocesso com um banco temporário e conversa JSON-RPC
por stdin/stdout, como um cliente MCP de verdade faria.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

AQUI = pathlib.Path(__file__).resolve().parent.parent
SRV = AQUI / "mcp" / "servidor.py"

tmp = tempfile.mkdtemp(prefix="saudade-mcp-")
env = dict(os.environ, SAUDADE_DB=os.path.join(tmp, "m.db"))

proc = subprocess.Popen([sys.executable, str(SRV)], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, text=True, env=env)
FALHAS = []
_id = 0


def rpc(method, params=None, notify=False):
    global _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _id += 1
        msg["id"] = _id
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    if notify:
        return None
    linha = proc.stdout.readline()
    return json.loads(linha)


def check(nome, cond):
    print(f"  {'ok   ' if cond else 'FALHA'} {nome}")
    if not cond:
        FALHAS.append(nome)


print("== handshake ==")
r = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "teste"}})
check("initialize responde serverInfo", r["result"]["serverInfo"]["name"] == "saudade")
rpc("notifications/initialized", notify=True)

print("== tools/list ==")
r = rpc("tools/list")
nomes = {t["name"] for t in r["result"]["tools"]}
check("6 tools expostas", len(nomes) == 6)
check("estado, add e buscar presentes", {"saudade_estado", "saudade_add", "saudade_buscar"} <= nomes)
check("nenhuma tool de delete/apply", not any("delete" in n or "apply" in n for n in nomes))

print("== ciclo real ==")
r = rpc("tools/call", {"name": "saudade_add", "arguments": {"entity": "Teste MCP", "tipo": "decisao", "texto": "MCP no ar"}})
check("add grava", not r["result"]["isError"] and "#1" in r["result"]["content"][0]["text"])
r = rpc("tools/call", {"name": "saudade_add", "arguments": {"entity": "Teste MCP", "tipo": "supersede", "texto": "#1 · mudamos de ideia"}})
check("supersede grava", not r["result"]["isError"])
r = rpc("tools/call", {"name": "saudade_buscar", "arguments": {"termo": "MCP"}})
check("buscar marca SUPERADO", "SUPERADO" in r["result"]["content"][0]["text"])
r = rpc("tools/call", {"name": "saudade_estado", "arguments": {}})
check("estado responde", "Estado vivo" in r["result"]["content"][0]["text"])
r = rpc("tools/call", {"name": "saudade_add", "arguments": {"entity": "Teste MCP", "tipo": "supersede", "texto": "#999 · fantasma"}})
check("erro vira isError, não crash", r["result"]["isError"])
r = rpc("ping")
check("ping", r["result"] == {})

proc.stdin.close()
proc.wait(timeout=10)
shutil.rmtree(tmp)

print()
if FALHAS:
    print(f"FALHOU: {FALHAS}")
    sys.exit(1)
print("servidor MCP ok")
