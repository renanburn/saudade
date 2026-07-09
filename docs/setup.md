# O que você precisa pra usar

A saudade tem três níveis. Cada um funciona sozinho, e cada um leva pro seguinte quando (e se) você quiser. Comece no menor que resolve o seu caso.

## Nível 0 · Papel ou Obsidian (zero instalação)

**Precisa de:** um arquivo de texto. Só.

As três regras funcionam num arquivo markdown, numa nota do Obsidian, até em caderno físico. Você numera as linhas à mão, risca sem apagar, mantém uma seção "estado" no topo. O guia passo a passo, com exemplo completo, está em [`sem-codigo.md`](sem-codigo.md).

**Ideal pra:** quem quer o método antes da ferramenta, quem não instala nada, quem vive no Obsidian.

**Limite honesto:** a partir de algumas centenas de linhas, buscar e projetar à mão cansa. É o sinal de subir de nível, e a migração é mecânica (o formato é o mesmo).

## Nível 1 · O CLI (a ferramenta deste repo)

**Precisa de:**

| item | por quê | já tem? |
|---|---|---|
| Python 3.8+ | roda o `saudade` | macOS e Linux: sim. Windows: [python.org](https://python.org) |
| SQLite | o banco | embutido no Python, não instala nada |
| Terminal | os comandos | sim |

Zero dependência externa, um arquivo, um banco local em `~/.saudade/memoria.db`. Sem conta, sem nuvem, sem chave de API. Seus fatos ficam na sua máquina.

```bash
git clone https://github.com/renanburn/saudade
ln -s "$PWD/saudade/bin/saudade" ~/.local/bin/saudade
saudade init
saudade add "Meu Projeto" observacao "começou hoje"
```

**Ideal pra:** quem opera projetos e quer memória consultável (`buscar`, `estado`, `rel audit`) sem depender de IA nenhuma. O CLI inteiro funciona sem modelo de linguagem.

**Opcional dentro deste nível:** o juiz do `saudade contradicoes --juiz sonnet` usa o [Claude Code CLI](https://claude.com/claude-code) se ele existir na máquina (aproveita a autenticação que você já tem, sem chave de API). Sem ele, o comando degrada pro relatório determinístico e continua útil.

## Nível 2 · Com um agente (o setup ideal)

É aqui que a saudade vira o que ela foi desenhada pra ser: a memória de trabalho de um agente que trabalha COM você.

**Precisa de:** o nível 1 + um agente que executa comandos (Claude Code é o caso de referência; qualquer agente com acesso a shell serve).

**O contrato, em três instruções no arquivo de instruções do seu agente** (`CLAUDE.md`, system prompt, ou equivalente):

```markdown
## Memória (saudade)
- Ao final de trabalho relevante, grave os fatos: `saudade add "Entity" tipo "texto"`.
  Um fato por linha. Tipos: decisao, pendencia, bloqueio, mudanca, observacao.
- Fato que deixou de ser verdade: `saudade add "Entity" supersede "#id · motivo"`.
  Tarefa cumprida: `saudade add "Entity" resolvido "#id · nota"`. Não confundir os dois.
- No começo da sessão, leia `saudade estado`. NUNCA leia o log inteiro.
```

Isso implementa as três camadas do método: o agente **escreve** deliberadamente durante o trabalho, **lê** a projeção no início da sessão, e a **curadoria** (o `contradicoes` semanal) propõe pra você decidir. Se o seu ambiente suporta hooks de início de sessão, injetar o `saudade estado` automaticamente é o refinamento natural.

**O que NÃO fazer no nível 2**, porque desfaz o desenho:

- não deixe o agente rodar `supersede` a partir do relatório de contradições sem você aprovar;
- não cole o log inteiro no contexto ("só dessa vez" vira sempre);
- não delegue a escrita a um processo que varre conversas e extrai fatos sozinho. A escrita deliberada é o que mantém a memória confiável; automatizar a escrita é importar os defeitos que este repo existe pra evitar.

## Resumo do setup ideal

Uma máquina com Python, um agente tipo Claude Code, três instruções no arquivo de instruções, e um humano que lê a projeção de vez em quando e responde às propostas de curadoria. A parte técnica é meia hora. A parte que sustenta o sistema é o hábito de gravar um fato por linha, e essa ninguém instala por você.
