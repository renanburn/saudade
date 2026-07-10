<p align="center">
  <img src="assets/hero.png" alt="Uma caderneta de armazém aberta em pixel art: uma linha riscada continua legível e brilha suave, enquanto a página ao lado recebe linhas novas" width="820">
</p>

<h1 align="center">saudade</h1>

<p align="center">
  Memória pra agentes de IA que nunca apaga, e mesmo assim sabe o que morreu.
</p>

<p align="center">
  <strong>A presença de uma ausência.</strong> O fato que deixou de ser verdade não some: fica, com a data em que valeu e o motivo de ter morrido.
</p>

<p align="center">
  <a href="https://github.com/renanburn/saudade/actions/workflows/testes.yml"><img src="https://github.com/renanburn/saudade/actions/workflows/testes.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue" alt="Licença MIT">
  <img src="https://img.shields.io/badge/mem%C3%B3ria-pt--BR-009c3b" alt="pt-BR">
  <img src="https://img.shields.io/badge/depend%C3%AAncias-zero-8a2be2" alt="Zero dependências">
  <a href="https://github.com/renanburn/gororoba"><img src="https://img.shields.io/badge/fam%C3%ADlia-gororoba-f9a825" alt="gororoba"></a>
  <a href="https://github.com/renanburn/tempero"><img src="https://img.shields.io/badge/fam%C3%ADlia-tempero-e25822" alt="tempero"></a>
</p>

---

**saudade** é a palavra que não traduz: a presença de uma ausência. É o nome certo pra memória que este repo propõe, porque todo sistema de memória de IA hoje erra de um dos dois lados: ou **lembra demais** (log que só cresce, fato morto misturado com fato vivo), ou **decide sozinho o que apagar** (extração automática que alucina, envelhece e se contradiz, por admissão dos próprios donos).

A saudade faz as duas coisas ao mesmo tempo: **nunca apaga, e sabe o que morreu**. O log é imutável. O fato errado não é deletado, é *superado*, com data e motivo. E o que a IA lê todo dia não é o log: é a projeção do que ainda vale.

**Não é banco vetorial, não é RAG, não é extração automática.** É uma caderneta de armazém: anota linha por linha, nunca rasura, e quando o cliente paga você não apaga a dívida, escreve "pago". O saldo é derivado de ler os eventos. O Brasil inventou event sourcing antes do nome.

## As três regras (levam 30 segundos, valem sem a ferramenta)

1. **Um fato por linha, com data.** Fato duplo não morre pela metade.
2. **Nunca apague. Marque o que morreu, dizendo por quê.**
3. **A IA lê a projeção, não o log.** O log guarda tudo; a projeção mostra o que vale agora.

Se você parar de ler aqui e for aplicar as três num arquivo de texto, o repo já cumpriu o papel. Tem um guia inteiro disso em [`docs/sem-codigo.md`](docs/sem-codigo.md).

## Veja rodando

```console
$ saudade add "Cliente ACME" decisao "proposta fechada em 7.350/mês"
+ #41  [2026-07-02 12:07] decisao :: proposta fechada em 7.350/mês

$ saudade add "Cliente ACME" supersede "#41 · cliente voltou atrás, renegociando do zero"
+ #58  [2026-07-09 09:14] supersede :: #41 · cliente voltou atrás, renegociando do zero
  ↳ supera #41

$ saudade buscar "proposta ACME"
#41  Cliente ACME  decisao  2026-07-02 12:07  ⊘ SUPERADO
  proposta fechada em 7.350/mês
  ⊘ morto por #58: cliente voltou atrás, renegociando do zero

$ saudade buscar "proposta ACME" --vigente
nada encontrado.
```

O `#41` continua no banco pra sempre. Ele só não engana mais ninguém.

```console
$ saudade estado          # a projeção: só o que vale AGORA (é isto que a IA recebe)
$ saudade contradicoes    # propõe supersedes quando dois fatos brigam; NUNCA aplica
$ saudade rel audit       # saúde do grafo de conexões, com janela de validade
$ saudade lint decisao "orçamento aprovado; e decidiu trocar de fornecedor"
aviso: parece haver DOIS fatos aqui (estado + decisão); separe em duas linhas
```

## Instalação

```bash
git clone https://github.com/renanburn/saudade
ln -s "$PWD/saudade/bin/saudade" ~/.local/bin/saudade
saudade init
```

Python 3.8+ e SQLite, que seu sistema já tem. Zero dependência, um arquivo. O banco fica em `~/.saudade/memoria.db` (mude com `SAUDADE_DB`).

O que você precisa pra cada nível de uso (papel/Obsidian → CLI → com um agente tipo Claude Code), e as três instruções que transformam seu agente num operador da caderneta: [`docs/setup.md`](docs/setup.md).

### Pro seu agente usar como tool (MCP)

```bash
claude mcp add saudade -- python3 /caminho/para/saudade/mcp/servidor.py
```

Seis tools: `saudade_estado`, `saudade_add`, `saudade_buscar`, `saudade_rel_add`, `saudade_rel_audit`, `saudade_contradicoes`. Nenhuma deleta, nenhuma aplica supersede em lote: o desenho de governança vale também na interface de máquina. Servidor em stdlib pura ([`mcp/servidor.py`](mcp/servidor.py)), zero dependência, testado em [`testes/mcp.py`](testes/mcp.py).

### Pro Claude Code, como skill

```bash
cp -r skill ~/.claude/skills/saudade
```

A skill ensina o agente a operar a caderneta: ler `estado` no início, gravar um fato por linha no fim, distinguir `resolvido` de `supersede`, e propor supersede na hora quando você disser algo que contradiz a memória, sem nunca aplicar sozinho.

## Por que existe: o incidente

Este repo nasceu de uma falha real, documentada em [`docs/o-incidente.md`](docs/o-incidente.md).

Em julho de 2026, o autor gravou na memória do seu agente uma decisão que mudava o rumo de uma das frentes do negócio. Seis dias depois voltou atrás, e a decisão nova foi gravada. As duas conviveram no log sem nada marcar a primeira como morta, e **quatro rodadas de planejamento foram construídas em cima da premissa revertida**: um plano inteiro com datas, papéis e um blueprint de 58 mil caracteres. Ninguém mentiu. O sistema só não sabia esquecer.

E o segundo ato é melhor: o detector de contradição construído pra consertar isso propôs, com confiança de 0,95, matar fatos que ainda eram meio verdade. A máquina propõe. O humano decide. Essa regra está no código.

## Como funciona por dentro

| Peça | O quê |
|---|---|
| **Log** | `observations` append-only. Fato = `[data] tipo :: texto`. INSERT sempre, DELETE nunca |
| **Eventos** | `resolvido :: #id` fecha tarefa · `supersede :: #id · motivo` mata fato. Estado é derivado, não guardado |
| **Semântica** | baixa superada **reabre** a pendência; #id só conta no início do texto |
| **Arestas** | `relations` com janela de validade: invalida com motivo, nunca deleta; a mesma aresta pode renascer (índice único parcial) |
| **Busca** | FTS5 + BM25, marcando `⊘ SUPERADO por #x: motivo`. Sem embeddings, de propósito |
| **Curadoria** | `contradicoes` acha fatos que brigam e propõe. Um humano aplica, ou não |

A especificação completa, sem uma linha de código, está em [`ESPECIFICACAO.md`](ESPECIFICACAO.md). A justificativa de cada escolha contra o estado da arte (com fonte) está em [`docs/estado-da-arte.md`](docs/estado-da-arte.md). O que a gente quebrou construindo está em [`docs/armadilhas.md`](docs/armadilhas.md).

## A família

| repo | régua |
|---|---|
| [gororoba](https://github.com/renanburn/gororoba) | a IA escreve com a **sua** voz |
| [tempero](https://github.com/renanburn/tempero) | **você** monta a sua régua |
| **saudade** | a IA lembra o que **foi** verdade, e quando deixou de ser |

## O que a saudade NÃO faz (e é escolha, não falta)

- **Não extrai memória automaticamente.** É onde os grandes sangram: memória alucinada, obsoleta, escrevível por injeção de prompt. Aqui, se ninguém escreveu o fato, não há memória. Esse é o custo, e ele é seu.
- **Não usa embeddings.** Recuperação semântica ampla dobra a taxa de violação induzida por memória (0,3-0,5 contra 0,1-0,2 de sistemas enviesados por recência). Busca aqui é texto + recência + estado.
- **Não aplica supersede sozinha.** Supersede errado é perda silenciosa de memória, pior que fato morto visível. Fato morto pelo menos você enxerga.
- **Não dá nota, não resume seu passado, não decide por você.** Ela lembra. Você decide.

## Licença

MIT. Anota, risca sem apagar, e leva a caderneta contigo.
