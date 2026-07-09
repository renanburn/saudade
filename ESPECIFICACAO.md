# saudade · a especificação

O formato inteiro, sem uma linha de código. Dá pra implementar em qualquer stack em uma tarde, ou seguir à mão num arquivo de texto. Quem implementa tudo daqui pode dizer que é compatível com a saudade.

## 1. O fato

Um fato é uma linha, imutável depois de escrita:

```
[YYYY-MM-DD HH:MM] tipo :: texto
```

- **Um fato por linha.** Se o texto junta duas coisas ("orçamento aprovado E decidiu trocar de fornecedor"), são duas linhas. Motivo prático: fato duplo não pode morrer pela metade.
- **A data é obrigatória** e é a data em que o fato passou a valer, não a de digitação (pode retro-datar).
- Cada fato tem um **id** estável e crescente. No SQLite é o rowid; no papel, você numera.

### Tipos que afirmam estado

| tipo | quando |
|---|---|
| `decisao` | algo foi decidido |
| `pendencia` | algo ficou em aberto, com dono |
| `bloqueio` | não anda até outra coisa resolver |
| `mudanca` | alteração estrutural concreta |
| `observacao` | fato relevante sem ação |
| `experimento` | testou, ainda não decidiu |
| `feedback` | orientação recebida de alguém |

### Tipos que são eventos sobre outro fato

| tipo | efeito |
|---|---|
| `resolvido :: #id · nota` | a pendência/bloqueio `#id` foi **cumprida** |
| `supersede :: #id · motivo` | o fato `#id` **deixou de ser verdade** |

E um tipo gerado por máquina, nunca à mão: `sintese` (resumo de compactação).

## 2. A regra da sequência líder

`#id` só tem efeito quando abre o texto: `#12 · motivo` ou `#12, #13 · motivo`. Mencionar `#12` no meio de uma frase não dá baixa em nada. Sem essa regra, qualquer citação casual mata fato por acidente.

## 3. O estado é derivado, nunca guardado

Não existe coluna de status. O estado atual é o resultado de ler os eventos:

1. Colete os alvos de todo `supersede` → conjunto **MORTOS**.
2. Colete os alvos de todo `resolvido` **que não esteja em MORTOS** → conjunto **BAIXADOS**.
3. Um fato **vale agora** se não está em MORTOS, e (sendo pendência/bloqueio) não está em BAIXADOS.

A ordem dos passos é a alma da especificação: um `resolvido` que foi ele mesmo superado **não dá baixa**, e a pendência **reabre**. A baixa estava errada; o log lembra disso também.

Diferença entre os dois eventos, que não pode borrar:

- `resolvido` fecha **tarefa**. Só afeta `pendencia` e `bloqueio`.
- `supersede` mata **fato**. Afeta qualquer tipo.

Confundir os dois é o erro mais comum. "Fizemos X" é baixa. "X deixou de ser verdade" é supersede.

## 4. Nada se apaga

- `INSERT` sempre. `DELETE` nunca. `UPDATE` nunca toca o texto do fato.
- Corrigir é **acrescentar**: um fato certo novo + um `supersede` no errado.
- Quebrar um fato duplo é: gravar as partes como fatos novos (retro-datados na data original), superar as partes mortas com a causa real, e superar o original apontando pros filhos.

O teste de conformidade mais simples: o banco de ontem é sempre um prefixo do banco de hoje.

## 5. As conexões (relations)

Aresta dirigida entre duas entities, com **janela de validade**:

```
source -[tipo]-> target · valid_from · invalidated_at? · motivo? · quem?
```

- Aresta que deixou de valer é **invalidada** (ganha data e motivo), nunca deletada.
- A mesma aresta pode **renascer** depois de morta, em outra janela. Implicação de schema: a unicidade vale só entre as **vigentes** (índice único parcial). UNIQUE de tabela quebra isso, porque a linha morta ocupa a chave.
- Vocabulário de tipos **controlado e pequeno** (11 na implementação de referência). Grafo com mais tipos de aresta do que arestas por tipo não carrega sinal.
- Cuidado com **direção**: "X é ferramenta de Y" significa "Y usa X". Remapear tipo sem conferir direção mente no grafo.

Com isso o banco responde as duas perguntas do modelo bi-temporal: *o que é verdade agora?* e *o que era verdade naquela data?*

## 6. A projeção

O que se entrega à IA (ou se lê de manhã) é uma **projeção determinística** do log, nunca o log:

- pendências e bloqueios **vivos** dos últimos N dias (30 é um bom padrão)
- decisões e mudanças **vivas** dos últimos M dias (7 é um bom padrão)
- nada de fato superado, nada de baixa, nada de síntese velha

Recência não é preguiça, é segurança: recuperação semântica ampla e sumarização no recall elevam mensuravelmente a taxa de erro induzido por memória. A projeção enviesada por recência e com baixa abstração é o desenho que menos erra.

## 7. A curadoria

A única camada onde entra um modelo de linguagem, e ele **propõe, nunca aplica**:

- detector de contradição: acha pares (fato antigo, fato novo com marca de reversão) e propõe `supersede` com motivo e confiança;
- o humano aplica, ou não. Confiança alta não é licença: o detector de referência já propôs matar, com 0,95, fatos que ainda eram meio verdade.

Compactação segue a mesma lei: **aditiva**. Threads velhas e fechadas ganham uma `sintese` e as originais são marcadas frias (leitores pulam). O texto original permanece, sempre.

## 8. Conformidade mínima

Uma implementação é saudade se:

1. o log é append-only (prefixo preservado);
2. `supersede` e `resolvido` seguem a sequência líder e a ordem do §3 (baixa superada reabre);
3. nenhuma operação padrão deleta fato ou aresta;
4. existe uma projeção que exclui mortos e baixados;
5. nenhum processo automático aplica `supersede` sem aprovação humana.

Embeddings, sync, interface, MCP: tudo opcional, tudo bem-vindo, nada disso é o núcleo.
