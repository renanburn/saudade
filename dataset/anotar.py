#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anotar.py — anotação cega dos pares, no navegador, sem instalar nada.

Sobe um servidor local (stdlib) com uma tela de anotação: um par por vez,
três botões, atalhos 1/2/3, progresso, desfazer. Salva cada resposta na hora
em dataset/anotacoes/<anotador>.jsonl (append-only, dá pra parar e voltar).

CEGO DE VERDADE: a tela nunca mostra rotulo_maquina nem notas. A ordem dos
pares é embaralhada por anotador (semente = nome), pra ordem não virar viés.

Uso:
    python3 dataset/anotar.py renan            # abre http://localhost:7864
    python3 dataset/anotar.py lirios --porta 7865
    python3 dataset/anotar.py --kappa          # concordância entre anotadores
    python3 dataset/anotar.py --consolidar     # grava rotulo_humano onde há consenso

Regra de desempate (a mesma do GUIA-ANOTACAO.md): na dúvida, nao_contradiz.
"""
import argparse
import hashlib
import html
import json
import pathlib
import random
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

AQUI = pathlib.Path(__file__).resolve().parent
PARES = AQUI / "pares.jsonl"
ANOTS = AQUI / "anotacoes"

ROTULOS = ["contradiz", "nao_contradiz", "parcial"]


def carrega_pares():
    return [json.loads(l) for l in PARES.read_text().splitlines() if l.strip()]


def carrega_respostas(anotador):
    f = ANOTS / f"{anotador}.jsonl"
    if not f.exists():
        return {}
    out = {}
    for l in f.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            out[r["par"]] = r  # última resposta vence (permite desfazer/reanotar)
    return {k: v for k, v in out.items() if v.get("rotulo")}


def ordem_do(anotador, pares):
    ids = [p["id"] for p in pares]
    rnd = random.Random(int(hashlib.sha256(anotador.encode()).hexdigest(), 16))
    rnd.shuffle(ids)
    return ids


PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>anotação cega · saudade</title>
<style>
  :root {{ --teal:#155e57; --ambar:#b8860b; --papel:#faf7f0; --tinta:#1a1a1a; --regua:#ddd6c8; }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ font-family: ui-monospace, "SF Mono", Menlo, monospace; background:var(--papel);
         color:var(--tinta); min-height:100vh; display:flex; flex-direction:column;
         align-items:center; padding:24px 16px 48px; }}
  .topo {{ width:100%; max-width:760px; display:flex; justify-content:space-between;
           align-items:baseline; gap:12px; }}
  .topo b {{ font-size:15px; }}
  .prog {{ color:#777; font-size:13px; }}
  .barra {{ width:100%; max-width:760px; height:4px; background:var(--regua);
            border-radius:2px; margin:10px 0 26px; overflow:hidden; }}
  .barra i {{ display:block; height:100%; width:{pct}%; background:var(--teal); }}
  .cartao {{ width:100%; max-width:760px; border:1px solid var(--regua); border-radius:12px;
             background:white; padding:20px 22px; margin-bottom:14px; }}
  .cartao .meta {{ font-size:12px; color:#888; margin-bottom:8px; letter-spacing:.4px; }}
  .cartao .texto {{ font-size:16.5px; line-height:1.55; font-family: Georgia, serif; }}
  .rotulo-antigo {{ border-left:4px solid var(--regua); }}
  .rotulo-novo {{ border-left:4px solid var(--teal); }}
  .pergunta {{ margin:18px 0 14px; font-size:14px; color:#555; text-align:center; }}
  .botoes {{ display:flex; gap:10px; width:100%; max-width:760px; flex-wrap:wrap; }}
  button {{ flex:1; min-width:180px; padding:16px 12px; font:inherit; font-size:14.5px;
            border-radius:10px; border:1.5px solid var(--regua); background:white;
            cursor:pointer; text-align:left; line-height:1.4; }}
  button:hover {{ border-color:var(--tinta); }}
  button b {{ display:block; font-size:15.5px; margin-bottom:4px; }}
  button .tecla {{ float:right; color:#999; font-size:12px; border:1px solid var(--regua);
                   border-radius:4px; padding:1px 7px; }}
  .rodape {{ margin-top:22px; display:flex; gap:18px; align-items:center; }}
  .rodape a, .rodape span {{ font-size:13px; color:#888; text-decoration:none; cursor:pointer; }}
  .rodape a:hover {{ color:var(--tinta); }}
  .lembrete {{ max-width:760px; width:100%; margin-top:26px; font-size:12.5px; color:#999;
               line-height:1.6; border-top:1px dashed var(--regua); padding-top:14px; }}
  .fim {{ text-align:center; margin-top:80px; max-width:560px; }}
  .fim h1 {{ font-size:22px; margin-bottom:14px; }}
  .fim p {{ color:#666; line-height:1.6; margin-bottom:10px; }}
</style></head><body>
{corpo}
<script>
function responde(r) {{
  fetch('/responde', {{method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{par:'{par_id}', rotulo:r}})}}).then(()=>location.reload());
}}
function desfaz() {{
  fetch('/desfaz', {{method:'POST'}}).then(()=>location.reload());
}}
document.addEventListener('keydown', e => {{
  if (e.key==='1') responde('contradiz');
  if (e.key==='2') responde('nao_contradiz');
  if (e.key==='3') responde('parcial');
  if (e.key==='u' || e.key==='Backspace') desfaz();
}});
</script></body></html>"""

CORPO_PAR = """
<div class="topo"><b>anotação cega · {anotador}</b><span class="prog">{feitos} de {total}</span></div>
<div class="barra"><i></i></div>
<div class="cartao rotulo-antigo">
  <div class="meta">ANTIGO · {ent_a} · {ts_a}</div>
  <div class="texto">{txt_a}</div>
</div>
<div class="cartao rotulo-novo">
  <div class="meta">NOVO · {ent_n} · {ts_n}</div>
  <div class="texto">{txt_n}</div>
</div>
<div class="pergunta">O fato NOVO faz o ANTIGO deixar de ser verdade?</div>
<div class="botoes">
  <button onclick="responde('contradiz')"><span class="tecla">1</span><b>contradiz</b>o antigo DEIXOU de ser verdade</button>
  <button onclick="responde('nao_contradiz')"><span class="tecla">2</span><b>não contradiz</b>convivem, ou é tarefa cumprida, ou outro assunto</button>
  <button onclick="responde('parcial')"><span class="tecla">3</span><b>parcial</b>o antigo tem duas partes e só UMA morreu</button>
</div>
<div class="rodape"><a onclick="desfaz()">← desfazer a última (u)</a></div>
<div class="lembrete">
  Tarefa CUMPRIDA não é contradição ("negociar X" → "X fechado" = não contradiz).
  Detalhe ou continuação não é contradição. Assunto parecido em OUTRO objeto não é contradição.
  Na dúvida, <b>não contradiz</b>. Não existe resposta certa escondida: o que você marcar É o dado.
</div>"""

CORPO_FIM = """
<div class="fim">
  <h1>Pronto. {total} de {total}.</h1>
  <p>Suas respostas estão em <code>dataset/anotacoes/{anotador}.jsonl</code>.</p>
  <p>Quando os outros anotadores terminarem:<br>
  <code>python3 dataset/anotar.py --kappa</code> mostra a concordância;<br>
  <code>python3 dataset/anotar.py --consolidar</code> grava o consenso no dataset.</p>
  <p>Pode fechar esta aba.</p>
</div>"""


def faz_handler(anotador, pares, ordem):
    por_id = {p["id"]: p for p in pares}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _html(self, corpo, par_id="", pct=0):
            page = PAGINA.format(corpo=corpo, par_id=par_id, pct=pct)
            b = page.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            resp = carrega_respostas(anotador)
            pendentes = [i for i in ordem if i not in resp]
            if not pendentes:
                self._html(CORPO_FIM.format(total=len(ordem), anotador=anotador), pct=100)
                return
            p = por_id[pendentes[0]]
            corpo = CORPO_PAR.format(
                anotador=html.escape(anotador),
                feitos=len(resp) + 1, total=len(ordem),
                ent_a=html.escape(p["antigo"]["entity"]), ts_a=p["antigo"]["ts"],
                txt_a=html.escape(p["antigo"]["texto"]),
                ent_n=html.escape(p["novo"]["entity"]), ts_n=p["novo"]["ts"],
                txt_n=html.escape(p["novo"]["texto"]),
            )
            self._html(corpo, par_id=p["id"], pct=round(len(resp) / len(ordem) * 100))

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            corpo = self.rfile.read(n).decode() if n else "{}"
            ANOTS.mkdir(exist_ok=True)
            f = ANOTS / f"{anotador}.jsonl"
            if self.path == "/responde":
                d = json.loads(corpo)
                if d.get("rotulo") in ROTULOS and d.get("par") in por_id:
                    from datetime import datetime
                    with open(f, "a") as fh:
                        fh.write(json.dumps({"par": d["par"], "rotulo": d["rotulo"],
                                             "anotador": anotador,
                                             "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                                            ensure_ascii=False) + "\n")
            elif self.path == "/desfaz":
                resp = carrega_respostas(anotador)
                feitos = [i for i in ordem if i in resp]
                if feitos:
                    ultimo = feitos[-1]
                    with open(f, "a") as fh:
                        fh.write(json.dumps({"par": ultimo, "rotulo": None,
                                             "anotador": anotador, "desfeito": True},
                                            ensure_ascii=False) + "\n")
            self.send_response(204)
            self.end_headers()

    return H


# ------------------------------------------------------------ kappa/consolidar


def cohen_kappa(a, b, chaves):
    iguais = sum(1 for k in chaves if a[k]["rotulo"] == b[k]["rotulo"])
    po = iguais / len(chaves)
    pe = 0.0
    for r in ROTULOS:
        pa = sum(1 for k in chaves if a[k]["rotulo"] == r) / len(chaves)
        pb = sum(1 for k in chaves if b[k]["rotulo"] == r) / len(chaves)
        pe += pa * pb
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def cmd_kappa():
    arquivos = sorted(ANOTS.glob("*.jsonl")) if ANOTS.exists() else []
    aa = {f.stem: carrega_respostas(f.stem) for f in arquivos}
    aa = {k: v for k, v in aa.items() if v}
    if len(aa) < 2:
        print(f"preciso de 2+ anotadores completos; tenho {list(aa) or 'nenhum'}.")
        for k, v in aa.items():
            print(f"  {k}: {len(v)} respostas")
        return
    nomes = list(aa)
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            a, b = aa[nomes[i]], aa[nomes[j]]
            comuns = sorted(set(a) & set(b))
            if not comuns:
                continue
            k = cohen_kappa(a, b, comuns)
            faixa = ("quase perfeita" if k > .8 else "substancial" if k > .6 else
                     "moderada" if k > .4 else "fraca")
            print(f"kappa {nomes[i]} × {nomes[j]}: {k:.2f} ({faixa}, Landis-Koch) sobre {len(comuns)} pares")
            desac = [c for c in comuns if a[c]["rotulo"] != b[c]["rotulo"]]
            if desac:
                print(f"  desacordos ({len(desac)}): {', '.join(desac[:12])}{' ...' if len(desac) > 12 else ''}")


def cmd_consolidar():
    arquivos = sorted(ANOTS.glob("*.jsonl")) if ANOTS.exists() else []
    aa = {f.stem: carrega_respostas(f.stem) for f in arquivos}
    aa = {k: v for k, v in aa.items() if v}
    if not aa:
        print("nenhuma anotação encontrada.")
        return
    pares = carrega_pares()
    gravou, conflito, faltando = 0, [], 0
    for p in pares:
        votos = [aa[n][p["id"]]["rotulo"] for n in aa if p["id"] in aa[n]]
        if len(votos) < len(aa):
            faltando += 1
            continue
        if len(set(votos)) == 1:
            p["rotulo_humano"] = votos[0]
            gravou += 1
        else:
            conflito.append((p["id"], dict(zip(aa, votos))))
    with open(PARES, "w") as f:
        for p in pares:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"consenso gravado em rotulo_humano: {gravou} pares · incompletos: {faltando}")
    if conflito:
        print(f"conflitos pra adjudicar em conversa ({len(conflito)}), rotulo_humano fica null neles:")
        for cid, votos in conflito:
            print(f"  {cid}: {votos}")
    print("\nO desempate de conflito é conversa entre os anotadores (adjudicação), nunca voto da máquina.")


def main():
    ap = argparse.ArgumentParser(description="anotação cega dos pares da saudade")
    ap.add_argument("anotador", nargs="?", help="seu nome (vira o arquivo de respostas)")
    ap.add_argument("--porta", type=int, default=7864)
    ap.add_argument("--kappa", action="store_true")
    ap.add_argument("--consolidar", action="store_true")
    ap.add_argument("--sem-navegador", action="store_true")
    a = ap.parse_args()

    if a.kappa:
        return cmd_kappa()
    if a.consolidar:
        return cmd_consolidar()
    if not a.anotador:
        ap.error("passe seu nome: python3 dataset/anotar.py renan")

    anotador = a.anotador.strip().lower()
    pares = carrega_pares()
    ordem = ordem_do(anotador, pares)
    feitos = len(carrega_respostas(anotador))
    url = f"http://localhost:{a.porta}"
    print(f"anotação cega · {anotador} · {feitos}/{len(ordem)} já feitas")
    print(f"abre: {url}  (atalhos: 1 contradiz · 2 não · 3 parcial · u desfaz)")
    print("Ctrl+C encerra; o progresso fica salvo, é só rodar de novo pra continuar.")
    srv = HTTPServer(("127.0.0.1", a.porta), faz_handler(anotador, pares, ordem))
    if not a.sem_navegador:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\naté mais. progresso salvo.")


if __name__ == "__main__":
    main()
