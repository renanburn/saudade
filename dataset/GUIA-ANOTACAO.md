# Guia de anotação — contradição em memória de trabalho

## O que você vai fazer

Pra cada par (`antigo` / `novo`), você recebe dois fatos sobre a mesma entidade,
registrados em datas diferentes. Sua tarefa é dizer se o fato `novo` **contradiz**
o fato `antigo`, e preencher `rotulo_humano` com um destes três valores:

- `"contradiz"`
- `"nao_contradiz"`
- `"parcial"`

**Não olhe o campo `rotulo_maquina`.** Ele é o palpite de um sistema automático
que você está avaliando. Se você ler o palpite antes de decidir, sua anotação
vira eco do sistema, não um julgamento independente. Cubra esse campo, anote
primeiro, só compare depois.

## O que é contradição

O fato `antigo` **deixou de ser verdade**. Não é sobre o mesmo assunto ter
mais informação, é sobre a informação de antes estar **errada agora**.

Pergunta de corte: *se eu só pudesse guardar um dos dois fatos, o `antigo`
teria que ser apagado porque ele não é mais real?* Se sim, é `contradiz`.

Exemplos de mecanismo de contradição:
- Decisão revertida ("vamos de X" → "decidiu ficar com Y")
- Fato corrigido ("o contrato foi assinado" → "na verdade nunca foi assinado")
- Cancelamento de algo que estava confirmado
- Troca de fornecedor, pessoa, preço ou data que invalida o valor anterior

Atenção: às vezes a reversão usa palavras completamente diferentes do fato
original. "Decidiu encerrar o contrato" e "seguiu firme e assumiu a linha nova" quase não dividem palavra: é o
projeto novo" não compartilham nenhuma palavra chave, mas o segundo mata o
primeiro. Não confie em repetição de vocabulário pra decidir.

## O que NÃO é contradição

- **Tarefa cumprida**: "vai negociar prazo com o fornecedor" → "negociação
  fechada, prazo renegociado". O segundo é o resultado do primeiro, não uma
  reversão.
- **Detalhe ou continuação**: "proposta enviada" → "proposta aceita com um
  ajuste no logo". Aceitar com ajuste não é recusar.
- **Outro objeto**: dois clientes parecidos, duas notas fiscais de meses
  diferentes, duas salas de estúdio diferentes. Se o fato novo fala de outra
  coisa (mesmo que pareça o mesmo assunto), o antigo continua valendo.
- **Atualização de quantidade que não inverte o fato**: "pediu 20 seringas"
  → "aumentou pra 35 seringas" não contradiz, só atualiza volume.
- **Palavra de reversão sobre OUTRA coisa**: "cancelou a reunião de
  briefing" não mata "assinou o contrato anual". A palavra "cancelou"
  engana, mas o alvo do cancelamento é diferente do fato antigo.

## O que é `parcial`

O fato `antigo` empilha **dois fatos numa frase só**, e o `novo` mata **só
um** dos dois. O outro fato não foi mencionado e continua valendo (não vira
`nao_contradiz` porque parte real morreu; não vira `contradiz` porque parte
real sobrevive).

Exemplo: "Orçamento aprovado; decidiu trocar de fornecedor" (dois fatos)
→ "Decidiu ficar" (mata só a decisão de sair; o status do contrato não foi
tocado). Isso é `parcial`, não `contradiz` puro.

Essa é a classe mais dura de acertar, e é ela que separa um detector de
contradição decente de um "deletador" ingênuo que apaga o fato antigo
inteiro sempre que vê qualquer sinal de mudança.

## Regra de desempate

Na dúvida real entre duas classes, **prefira `nao_contradiz`**. O custo de
apagar um fato que ainda era verdade é maior que o custo de manter um fato
que já morreu (esse segundo erro se corrige sozinho quando aparecer o
próximo update). Só marque `contradiz` ou `parcial` quando o texto sustenta
isso sem esforço de interpretação.

## 6 exemplos comentados

**1. contradiz** — antigo: "Decidiu encerrar o contrato de consultoria, quer
vender a parte." novo: "Vai ficar e tocar o projeto novo." → O antigo (saída)
não é mais real. Vocabulário totalmente diferente, mas é reversão direta.

**2. contradiz** — antigo: "Contrato foi assinado dia 14/03." novo: "Na
verdade o contrato nunca foi assinado, cliente sumiu." → Correção de fato,
não desenvolvimento.

**3. nao_contradiz** — antigo: "Vai negociar prazo de entrega, atraso de 2
semanas." novo: "Negociação fechada, prazo renegociado pra 10 dias." → O
novo é o desfecho da mesma tarefa, não uma reversão dela.

**4. nao_contradiz** — antigo: "Assinou o contrato anual de gestão de
redes." novo: "Cancelou a reunião de briefing dessa semana." → "Cancelou"
mira a reunião, não o contrato. Objeto diferente dentro do mesmo tema.

**5. parcial** — antigo: "App vai ter versão paga e parceria com banco
digital pro lançamento." novo: "Parceria com o banco caiu." → Só a parceria
morreu; a versão paga não foi mencionada e segue valendo.

**6. parcial** — antigo: "Vai abrir uma segunda unidade e contratar mais
duas esteticistas." novo: "Engavetou o plano da segunda unidade." → Só a
expansão física morreu; a contratação não foi tocada.

## Checklist rápido antes de marcar

1. Os dois fatos falam da mesma entidade e do mesmo objeto específico?
   Se não → `nao_contradiz`.
2. O fato antigo tem mais de uma afirmação embutida? Se sim, cheque cada
   uma separadamente antes de decidir entre `contradiz` e `parcial`.
3. Existe palavra de reversão (cancelou, mudou, desistiu, na verdade) mas
   ela mira em algo diferente do fato antigo? Se sim → `nao_contradiz`.
4. Só depois de passar pelos 3 pontos acima, preencha `rotulo_humano`.
