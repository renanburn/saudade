# Changelog

## v0.2.0 · 2026-07-09

- **Servidor MCP** (`mcp/servidor.py`): a caderneta como tools de qualquer agente compatível.
  Stdlib pura, 6 tools, nenhuma destrutiva. Teste de protocolo em `testes/mcp.py`.
- **Skill pro Claude Code** (`skill/SKILL.md`): o contrato de operação da caderneta
  (estado no início, um fato por linha no fim, resolvido ≠ supersede, propor sem aplicar).
- **Dataset de avaliação** (`dataset/`): 72 pares de contradição/não-contradição em pt-BR,
  com guia de anotação cega. `rotulo_humano` nulo de propósito: o número que vale sai
  da anotação humana, não da pré-anotação de máquina.
- **Harness de avaliação** (`testes/avaliar.py`): mede o recall do funil determinístico
  (FN é contradição que ninguém verá; FP custa só tempo de juiz). Gate de recall ≥ 0,80.
- Dogfooding comprovado: o banco de produção do autor roda nos comandos da saudade sem adaptação.

## v0.1.0 · 2026-07-09

Primeira versão. Nasceu de um incidente real (ver `docs/o-incidente.md`) e de uma
comparação com o estado da arte feita no mesmo dia; o schema e a semântica rodaram
primeiro em produção na memória de trabalho do autor, e só depois viraram este repo.

- Log append-only com eventos `resolvido` (fecha tarefa) e `supersede` (mata fato)
- Semântica de estado derivado, incluindo a regra da baixa superada que REABRE a pendência
- Relations bi-temporais: invalidação com motivo, índice único parcial, aresta pode renascer
- Busca FTS5/BM25 com consciência de estado (`⊘ SUPERADO por #x: motivo`, `--vigente`)
- Projeção `estado` (o que a IA lê; nunca o log)
- Detector de contradição que PROPÕE supersedes (juiz opcional via Claude Code CLI); nunca aplica
- Compactação aditiva (síntese + esfriamento; nada apagado)
- `lint` de higiene do fato (um fato por linha, sequência líder, alvo existente)
- Especificação completa independente de código (`ESPECIFICACAO.md`)
- Guia sem código (Obsidian/arquivo texto), setup em 3 níveis, estado da arte com fonte, armadilhas
