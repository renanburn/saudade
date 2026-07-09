#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""saudade-mcp — servidor MCP (stdio) da saudade. Stdlib pura, zero dependência.

Expõe a caderneta como tools pra qualquer agente compatível com MCP
(Claude Code, Claude Desktop, etc):

    saudade_estado        a projeção: o que vale agora (leia no início da sessão)
    saudade_add           grava um fato (append-only, com lint)
    saudade_buscar        busca com consciência de estado (marca o que morreu)
    saudade_rel_add       conecta duas entities
    saudade_rel_audit     saúde do grafo
    saudade_contradicoes  pares suspeitos (determinístico; PROPÕE, nunca aplica)

Registro no Claude Code:
    claude mcp add saudade -- python3 /caminho/para/saudade/mcp/servidor.py

Protocolo: JSON-RPC 2.0, uma mensagem por linha em stdin/stdout (transporte
stdio do MCP). Sem SDK de propósito: o protocolo necessário cabe em 100 linhas
e a filosofia do repo é dependência zero.

Segurança de desenho: NENHUMA tool aplica supersede em lote nem deleta nada.
`saudade_add` grava um fato por chamada, e supersede exige #id explícito no
texto, igual no CLI. A máquina propõe (saudade_contradicoes); o humano decide.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(os.path.dirname(AQUI), "bin", "saudade")

loader = importlib.machinery.SourceFileLoader("saudade_cli", CLI)
spec = importlib.util.spec_from_loader("saudade_cli", loader)
sd = importlib.util.module_from_spec(spec)
sys.modules["saudade_cli"] = sd
loader.exec_module(sd)

PROTOCOLO = "2025-06-18"
INFO = {"name": "saudade", "version": "0.2.0"}


def roda_cli(argv):
    """Roda um comando do CLI capturando stdout/stderr como texto (sem ANSI:
    stdout redirecionado não é TTY). SystemExit vira erro legível, não morte."""
    out, err = io.StringIO(), io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            sd.main(argv)
    except SystemExit as e:
        code = int(e.code or 0)
    texto = out.getvalue().strip()
    if err.getvalue().strip():
        texto = (texto + "\n" + err.getvalue().strip()).strip()
    return code, texto or "(sem saída)"


TOOLS = [
    {
        "name": "saudade_estado",
        "description": ("A projeção da memória: pendências, bloqueios e decisões que valem AGORA. "
                        "Leia no início da sessão. Nunca peça o log inteiro."),
        "inputSchema": {"type": "object", "properties": {
            "dias_pendencia": {"type": "integer", "description": "janela de pendências/bloqueios (padrão 30)"},
            "dias_decisao": {"type": "integer", "description": "janela de decisões/mudanças (padrão 7)"},
        }},
    },
    {
        "name": "saudade_add",
        "description": ("Grava UM fato na caderneta (append-only). Um fato por chamada. "
                        "Tipos de estado: decisao, pendencia, bloqueio, mudanca, observacao, experimento, feedback. "
                        "Eventos: resolvido (tarefa cumprida) e supersede (fato deixou de ser verdade), "
                        "ambos com '#id · motivo' no início do texto. Não confunda os dois."),
        "inputSchema": {"type": "object", "required": ["entity", "tipo", "texto"], "properties": {
            "entity": {"type": "string", "description": "de quem é o fato (projeto, cliente, tema)"},
            "tipo": {"type": "string"},
            "texto": {"type": "string", "description": "o fato, curto e único"},
            "at": {"type": "string", "description": "retro-datar: 'YYYY-MM-DD HH:MM' (opcional)"},
        }},
    },
    {
        "name": "saudade_buscar",
        "description": ("Busca full-text na caderneta, marcando o que está SUPERADO e por quê. "
                        "vigente=true esconde fatos mortos e pendências resolvidas."),
        "inputSchema": {"type": "object", "required": ["termo"], "properties": {
            "termo": {"type": "string"},
            "vigente": {"type": "boolean"},
            "tipo": {"type": "string"},
            "entity": {"type": "string"},
            "limit": {"type": "integer"},
        }},
    },
    {
        "name": "saudade_rel_add",
        "description": ("Conecta duas entities com tipo do vocabulário controlado "
                        "(pertence a, depende de, bloqueado por, deriva de, alimenta, consome, "
                        "implementa, documenta, opera, usa, atende)."),
        "inputSchema": {"type": "object", "required": ["source", "target", "tipo"], "properties": {
            "source": {"type": "string"}, "target": {"type": "string"}, "tipo": {"type": "string"},
        }},
    },
    {
        "name": "saudade_rel_audit",
        "description": "Saúde do grafo: vocabulário, densidade, bloqueios e dependências a revisar.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "saudade_contradicoes",
        "description": ("Pares de fatos que podem se contradizer (determinístico, sem LLM). "
                        "PROPÕE apenas: aplicar supersede é decisão do humano, nunca sua."),
        "inputSchema": {"type": "object", "properties": {
            "dias": {"type": "integer", "description": "janela do fato novo (padrão 60)"},
        }},
    },
]


def chama_tool(nome, args):
    if nome == "saudade_estado":
        argv = ["estado"]
        if args.get("dias_pendencia"):
            argv += ["--dias-pendencia", str(args["dias_pendencia"])]
        if args.get("dias_decisao"):
            argv += ["--dias-decisao", str(args["dias_decisao"])]
    elif nome == "saudade_add":
        argv = ["add", args["entity"], args["tipo"], args["texto"]]
        if args.get("at"):
            argv += ["--at", args["at"]]
    elif nome == "saudade_buscar":
        argv = ["buscar", args["termo"]]
        if args.get("vigente"):
            argv.append("--vigente")
        if args.get("tipo"):
            argv += ["--tipo", args["tipo"]]
        if args.get("entity"):
            argv += ["--entity", args["entity"]]
        if args.get("limit"):
            argv += ["--limit", str(args["limit"])]
    elif nome == "saudade_rel_add":
        argv = ["rel", "add", args["source"], args["target"], args["tipo"]]
    elif nome == "saudade_rel_audit":
        argv = ["rel", "audit"]
    elif nome == "saudade_contradicoes":
        argv = ["contradicoes", "--juiz", "off"]
        if args.get("dias"):
            argv += ["--dias", str(args["dias"])]
    else:
        return True, f"tool desconhecida: {nome}"
    code, texto = roda_cli(argv)
    return code != 0, texto


def responde(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    # garante que o banco existe; se não, cria (primeira sessão não deve quebrar)
    if not os.path.exists(sd.DB):
        roda_cli(["init"])
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            msg = json.loads(linha)
        except json.JSONDecodeError:
            continue
        metodo, id_ = msg.get("method"), msg.get("id")
        if metodo == "initialize":
            responde(id_, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOLO),
                "capabilities": {"tools": {}},
                "serverInfo": INFO,
            })
        elif metodo == "notifications/initialized":
            continue
        elif metodo == "ping":
            responde(id_, {})
        elif metodo == "tools/list":
            responde(id_, {"tools": TOOLS})
        elif metodo == "tools/call":
            p = msg.get("params", {})
            is_err, texto = chama_tool(p.get("name"), p.get("arguments") or {})
            responde(id_, {"content": [{"type": "text", "text": texto}], "isError": is_err})
        elif id_ is not None:
            responde(id_, error={"code": -32601, "message": f"método não suportado: {metodo}"})


if __name__ == "__main__":
    main()
