# O método

## Por que log imutável

Todo sistema de memória de IA cai num de dois buracos. Ou lembra demais: guarda cada
frase, cada rascunho, cada ideia que morreu no meio do caminho, e depois não separa mais
o que vale do que já foi superado. Ou decide sozinho o que apagar: um resumo automático,
um score de importância, um "isso não parece relevante" calculado sem ninguém olhar.

Os dois quebram a mesma coisa. Se a memória pode ter apagado algo sem avisar, toda
resposta que ela dá carrega uma dúvida embutida: será que isso ainda é verdade, ou foi
uma das coisas que sumiram?

saudade não tenta escolher o que apagar. Não apaga nada. Não existe UPDATE de conteúdo,
não existe DELETE. Existe INSERT. Cada fato que entra, fica. O que muda com o tempo não
é o fato: é o que se lê dele.

## A caderneta do armazém

A imagem que explica o resto do sistema é a caderneta de fiado de um armazém de bairro.
O dono não apaga a compra quando o freguês paga. Ele anota outra linha: "pago dia 12".
A dívida original continua escrita, riscada ou marcada, mas continua lá. Quem quer saber
o saldo não pergunta pro dono: soma as linhas. Compra, compra, pagamento, compra, estorno
do pagamento porque o cheque voltou. O saldo é derivado de ler o histórico inteiro, nunca
de uma célula que alguém sobrescreve.

Isso é event sourcing. O Brasil inventou a prática décadas antes do nome chegar de fora,
em qualquer armazém, qualquer padaria com caderno de fiado. "Pago" não apaga a dívida:
adiciona um evento que, ao ser lido junto com o resto, faz a dívida parar de aparecer no
saldo. Se o pagamento for revertido, some outro evento, e a dívida volta a aparecer. Nunca
se mexe na linha original.

saudade grava fato exatamente assim. Uma tabela `observations`, cada linha um evento
datado: `[YYYY-MM-DD HH:MM] tipo :: texto`. O que parece "editar" ou "apagar" um fato é,
por baixo, sempre uma linha nova que muda como as linhas anteriores são lidas.

## Os dois eventos

Dois tipos de evento agem sobre um fato anterior, e são fáceis de confundir porque os
dois têm cara de "isso aqui não vale mais". Não são a mesma coisa.

**`resolvido`** fecha uma tarefa. Só se aplica a `pendencia` e `bloqueio`, os dois tipos
que pedem baixa. Não diz que o fato estava errado, diz que ele foi cumprido.

```
saudade add "Estúdio Aurora" pendencia "fechar contrato até junho"
# grava #10

saudade add "Estúdio Aurora" resolvido "#10 · contrato assinado dia 20"
# #10 some do estado vivo: virou tarefa cumprida
```

**`supersede`** mata um fato. Qualquer tipo: decisão, mudança, observação, experimento,
até um `resolvido` anterior. Diz que aquele fato deixou de ser verdade, não que foi
concluído.

```
saudade add "Estúdio Aurora" decisao "mantém o plano de expansão até 2027"
# grava #40

saudade add "Estúdio Aurora" supersede "#40 · premissa caiu, expansão adiada sem prazo"
# #40 não aparece mais no estado: não é que a decisão foi "cumprida",
# é que ela deixou de valer
```

A diferença prática: `resolvido` faz uma pendência sumir porque o trabalho acabou.
`supersede` faz qualquer fato sumir porque ele estava errado, ou o mundo mudou debaixo
dele. Uma tarefa cumprida não devia poder ser "matada" como se nunca tivesse existido; um
fato falso não devia continuar contando como pendente. Dois botões, dois efeitos, e o
sistema recusa `resolvido` num tipo que não é pendência ou bloqueio.

## A cadeia completa

O ponto mais contraintuitivo do desenho aparece quando os dois eventos se encadeiam.
Segue um caso real de uso, passo a passo:

```
#10  pendencia  "fechar contrato Aurora até junho"
#15  resolvido  "#10 · contrato assinado dia 20"          -> #10 fecha
#22  supersede  "#15 · assinatura era só verbal, não saiu do papel"  -> #15 morre
#30  supersede  "#10 · decidiu não fechar mais, foco mudou"          -> #10 morre de vez
```

Depois de `#15`, o sistema lê `#10` como resolvido. Some do estado vivo.

Depois de `#22`, o evento que dava baixa em `#10` foi ele mesmo superado. A baixa estava
errada: o contrato nunca saiu do papel. `#10` **reabre**. Volta a aparecer como pendência
viva, sem que ninguém precise recriar a linha original.

Depois de `#30`, alguém mata `#10` diretamente. Agora não é mais "pendente de novo", é
morto: a decisão de fechar contrato deixou de valer, ponto final. Não reaparece em nenhum
estado futuro, porque `supersede` derruba o fato inteiro, não só a baixa dele.

Essa reabertura automática é a razão de existir do sistema. Sem ela, uma baixa errada
fica pra sempre esquecida, e a pendência real fica invisível pra IA que devia estar de
olho nela.

## Bi-temporal na prática

Todo fato tem dois tempos: quando ele era (ou passou a ser) verdade no mundo, e quando o
sistema ficou sabendo disso. Normalmente os dois coincidem, mas nem sempre. Se alguém
descobre em junho que uma decisão de março já não vale desde abril, o evento `supersede`
entra em junho (é quando o sistema aprendeu), mas o motivo dele fala de abril (é quando
deixou de valer no mundo).

Nas relations isso é explícito no schema: `valid_from` marca quando a aresta passou a
valer, `invalidated_at` marca quando parou. Exemplo:

```
saudade rel add "Estúdio Aurora" "Selo Baião" "atende"
# valid_from = 2026-03-01

saudade rel invalidate 7 --reason "contrato encerrado" --by humano
# invalidated_at = 2026-06-15
```

"O que é verdade agora?" é `saudade rel list`: só mostra arestas com `invalidated_at IS
NULL`, isto é, ainda vigentes. "O que era verdade em março?" é reconstruir a mesma
pergunta com um corte de data: pegar `rel list --todas` e filtrar toda aresta cujo
`valid_from` seja anterior a março e cujo `invalidated_at` seja nulo ou posterior a
março. A aresta Aurora -[atende]-> Selo Baião entra nessa foto mesmo depois de invalidada em junho,
porque em março ela ainda valia. O log não muda, só a janela de leitura muda.

Nas observations o mesmo raciocínio vale usando o `ts` de cada evento: o fato original
carrega o tempo em que passou a ser verdade, o `supersede` carrega o tempo em que parou.
Perguntar "o que a memória sabia em março" é filtrar os fatos por `ts <= março` antes de
calcular quem está morto ou baixado, não aplicar o filtro depois.

## A projeção

`saudade estado` é o único comando pensado pra ser lido por uma IA todo dia. Ele não
devolve o log: devolve bloqueios e pendências dos últimos 30 dias, decisões e mudanças
dos últimos 7, todos já filtrados pelos eventos vivos (fato morto e pendência baixada não
aparecem). É o inverso de "manda tudo e deixa o modelo separar o que interessa".

Isso existe por dois motivos técnicos, não só estético. Um: contexto grande degrada
recuperação. Quanto mais fato solto entra na janela, mais fica difícil pro modelo achar o
que importa entre o que é ruído, mesmo quando a informação certa está lá dentro. Dois:
recência reduz risco. Um fato de seis meses atrás tem mais chance de já ter sido
superado, mesmo que ninguém tenha registrado isso ainda; jogar peso pro que é recente
protege contra fato velho e morto que ninguém lembrou de matar.

A IA nunca deveria ler `saudade buscar` sem `--vigente`, e nunca deveria receber o banco
inteiro como contexto. O log é a fonte de verdade. O `estado` é o que se injeta.

## O que fica de fora por desenho

**Extração automática.** Fato só entra quando alguém, humano ou agente, escreve a linha
de propósito. Não existe parser lendo conversa solta e decidindo sozinho "isso aqui
parece um fato, vou gravar". É trabalho a mais em troca de nunca gravar lixo sem
querer.

**Embeddings.** Busca é FTS5 com BM25, léxica, não vetorial. `saudade buscar` acha o que
compartilha palavra com o termo buscado, não o que é "semanticamente parecido". Fica mais
pobre pra sinônimo distante, mas mais previsível: o que acende é o que devia acender.

**Score de importância.** Não existe peso calculado de "isso é mais relevante que
aquilo". O que sobe pro topo do `estado` é tipo e recência, critério simples e auditável.
Um score aprendido decide sozinho o que importa, e é exatamente esse tipo de decisão
silenciosa que o log imutável existe pra evitar.
