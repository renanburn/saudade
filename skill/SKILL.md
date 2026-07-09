---
name: saudade
description: >-
  Memória de trabalho append-only com invalidação (saudade). Use quando o usuário
  pedir pra "lembrar", "gravar decisão", "o que ficou pendente", "o que decidimos
  sobre X", "isso mudou/não vale mais", ou ao FIM de trabalho relevante (gravar os
  fatos da sessão). Também quando notar contradição entre um fato da memória e o
  que o usuário acabou de dizer. Trigger: /saudade, "grava isso", "anota na
  caderneta", "o que vale hoje", "isso caiu".
---

# saudade · como operar a caderneta

Você escreve na memória do usuário. As regras abaixo não são estilo, são o que
mantém a memória confiável. O CLI é `saudade` (se não estiver no PATH, use o
caminho do repo: `bin/saudade`).

## No início da sessão (ou quando pedir contexto)

```bash
saudade estado
```

É a projeção do que vale AGORA. **Nunca** leia o log inteiro, nunca despeje o
banco no contexto. Se precisar de algo específico, busque:

```bash
saudade buscar "termo" --vigente     # esconde o que já morreu
saudade buscar "termo"               # mostra tudo, marcando ⊘ SUPERADO
```

## Ao final de trabalho relevante

Grave os fatos duráveis da sessão. **Um fato por linha.** Se a frase junta duas
coisas ("X aconteceu e decidimos Y"), são DUAS chamadas.

```bash
saudade add "Nome da Entity" decisao "o que foi decidido, curto e direto"
saudade add "Nome da Entity" pendencia "o que ficou aberto, com dono"
```

Tipos: `decisao` · `pendencia` · `bloqueio` · `mudanca` · `observacao` ·
`experimento` · `feedback`. Entity = projeto, cliente ou tema; antes de criar
uma nova, confira se não é variação de uma existente (o CLI trava, respeite o
aviso em vez de passar `--force`).

## Quando algo deixa de valer (a parte que importa)

Dois eventos, e confundi-los corrompe a memória:

```bash
# a TAREFA foi cumprida (pendência/bloqueio):
saudade add "Entity" resolvido "#42 · feito, nota curta"

# o FATO deixou de ser verdade (qualquer tipo):
saudade add "Entity" supersede "#42 · motivo real da reversão"
```

"Fizemos X" é `resolvido`. "X não é mais verdade" é `supersede`. O `#id` vai no
INÍCIO do texto (ache o id com `saudade buscar`). Nada é apagado: o fato morto
fica no log, marcado, e some das projeções.

Se o usuário disser algo que contradiz um fato da memória ("na verdade decidi
ficar", "aquilo caiu", "não vamos mais fazer Y"), NÃO deixe passar: busque o
fato antigo e proponha o supersede na hora, com o id. Fato morto sem supersede
envenena todas as sessões seguintes.

## O que você NUNCA faz

1. **Nunca aplica supersede em lote** nem a partir do relatório de
   `saudade contradicoes` sem o usuário aprovar item a item. O comando propõe;
   o humano decide. Confiança alta não é licença: fatos que empilham verdade e
   mentira quebram ao serem superados inteiros.
2. **Nunca deleta nada** (não existe delete, e é de propósito).
3. **Nunca inventa memória**: se não está no `estado` nem na busca, você não sabe.
4. **Nunca despeja o log inteiro no contexto.**

## Curadoria (quando o usuário pedir revisão)

```bash
saudade contradicoes            # pares suspeitos, determinístico
saudade rel audit               # saúde do grafo de conexões
saudade compactar               # dry-run de compactação (aditiva)
```

Apresente as propostas, aplique só o que o usuário aprovar, uma a uma.
