# Armadilhas

Livro de armadilhas do saudade. Cada entrada é uma lição que custou construir errado
primeiro. Formato: Sintoma, o que apareceu quebrado. Causa, por que quebrou. Regra, o que
o código ou o processo faz agora pra não quebrar de novo.

## 1. Dois fatos numa linha

**Sintoma:** um fato como "o acerto ficou no verbal E decidi encerrar a frente" não dá
pra superar direito. Quando um dos dois pedaços vira mentira, o `supersede` mata o fato
inteiro, os dois pedaços juntos.

**Causa:** um evento `supersede` mira o fato pelo `#id`, não por pedaço de frase. Não tem
como matar só metade de uma linha.

**Regra:** um fato por linha. Se a frase tem "e decidiu", "mas resolveu", ou qualquer
conector que junta dois estados diferentes, é dois fatos, viram duas linhas. O `lint`
avisa quando detecta esse padrão (`saudade lint tipo "texto"`), mas o aviso não bloqueia:
quem grava decide.

## 2. Marca de reversão com acento

**Sintoma:** o detector de contradição não reconhecia "correção" nem "não vai mais" como
sinal de reversão, mesmo estando na lista de marcas.

**Causa:** o texto do fato é desacentuado antes de comparar (`desacentua()`), mas a marca
na lista estava escrita com acento. Comparação nunca batia. Bug silencioso: o código
rodava sem erro, só nunca acendia.

**Regra:** toda marca de reversão fica em ASCII puro na lista (`MARCAS_FORTES`,
`MARCAS_FRACAS`), sem acento, sem cedilha. E se testa com o caso real que motivou a marca
entrar na lista, não só com o texto ideal.

## 3. Contradição não é semelhança de assunto

**Sintoma:** o par "decidiu sair" vs "decidiu ficar", que é exatamente o par que devia
acender o alarme de contradição, ficava de fora do ranking. Pares que só falavam do mesmo
assunto sem se contradizer subiam na frente.

**Causa:** o ranking usava sobreposição de vocabulário (quantas palavras os dois fatos
compartilham) como proxy de contradição. Mas "sair" e "ficar" quase não compartilham
palavra nenhuma: são o oposto exato um do outro, e o oposto exato tende a ser dito com
palavras diferentes, não com as mesmas.

**Regra:** marca de reversão tem prioridade absoluta sobre score de similaridade. Um par
com marca forte (`forca_marca() == 2`) entra na lista de candidatos mesmo com score zero,
antes de qualquer par ranqueado por vocabulário comum, e nunca é cortado pelo teto de
pares.

## 4. Janela por recência global

**Sintoma:** ao montar os candidatos pra um fato novo de uma entity, a janela enchia com
fatos de outras entities só citadas de passagem, e empurrava pra fora os fatos da própria
entity, que eram o que de fato importava comparar.

**Causa:** ordenar candidatos só por recência global, sem separar "fato desta entity" de
"fato de entity mencionada", deixa qualquer entity barulhenta dominar a janela de
qualquer outra.

**Regra:** primeiro os fatos da própria entity, por recência, depois os das entities
citadas no texto, depois o resto ranqueado por peso. Nessa ordem, sempre.

## 5. #id no meio do texto

**Sintoma:** um fato que só menciona "#853" no meio da frase, tipo "isso segue a linha do
#853", dava baixa acidental nele, ou parecia que devia dar.

**Causa:** procurar `#\d+` em qualquer lugar do texto acha menção casual junto com alvo
real. Sem distinguir os dois, qualquer citação vira baixa fantasma.

**Regra:** só a sequência LÍDER de `#id`, no início do texto, conta como alvo
(`HEAD_RE = ^((?:#\d+[\s,]*)+)`). "#12 · motivo" no começo é alvo. "…segue a linha do
#12" no meio não é. `resolvido` e `supersede` exigem essa sequência líder pra serem
aceitos; o `add` recusa gravar se não tiver.

## 6. Confiança do juiz não é licença pra apagar

**Sintoma:** o detector de contradição propôs matar dois fatos inteiros com confiança
entre 0,85 e 0,95, número que parece alto o bastante pra confiar de olhos fechados. Os
dois casos empilhavam um fato ainda vivo junto com um já morto: aplicar o supersede
proposto mataria o vivo também.

**Causa:** confiança alta de um juiz automático não garante que o par inteiro seja seguro
de matar. Ela mede a chance de contradição entre dois textos, não verifica se algum dos
dois carrega mais de um fato dentro (ver armadilha 1).

**Regra:** `saudade contradicoes` só propõe. Nunca aplica. Toda saída vem com o comando
pronto pra copiar, e quem decide gravar o `supersede` é sempre um humano lendo o par. A
máquina propõe, o humano decide, sem exceção pra número de confiança alto.

## 7. UNIQUE de tabela vs aresta que renasce

**Sintoma:** depois de invalidar uma relation e tentar recriar a mesma aresta mais tarde
(mesma origem, mesmo destino, mesmo tipo), a gravação falhava.

**Causa:** um `UNIQUE(source, target, relation_type)` de tabela inteira não distingue
aresta viva de aresta morta. A linha invalidada continua ocupando a chave única,
travando qualquer nova aresta idêntica, mesmo numa janela de tempo totalmente diferente.

**Regra:** índice único parcial: `CREATE UNIQUE INDEX idx_rel_ativa ON
relations(source, target, relation_type) WHERE invalidated_at IS NULL`. Só arestas
vigentes competem pela unicidade. Uma aresta pode nascer, morrer, e renascer meses
depois, cada janela com seu próprio `valid_from`.

## 8. delete_relation

**Sintoma:** apagar uma aresta que não valia mais também apagava o registro de que ela
tinha existido. Sem jeito de responder depois "quando isso começou a valer" ou "por que
parou".

**Causa:** DELETE tira a linha do banco. Não sobra histórico nenhum, só o silêncio de uma
aresta que nunca apareceu.

**Regra:** nunca apagar relation. Invalidar: `saudade rel invalidate <id> --reason "..."`
grava `invalidated_at` e `invalid_reason`, a linha continua no banco, `rel list --todas`
continua mostrando ela marcada como morta. A conexão existiu, e o registro de que existiu
não desaparece só porque parou de valer.

## 9. O detector overfitou no vocabulário do próprio dono

**Sintoma:** o detector de contradição rodava bem no banco do autor. No primeiro
dataset externo (72 pares, 6 domínios), recall de 0,23: perdeu 31 de 40 contradições.

**Causa:** a lista de marcas de reversão foi colecionada lendo o PRÓPRIO banco.
"Decidiu ficar", "caiu a premissa" é como o autor escreve. O mundo escreve
"recuou", "cancelou", "trocou de fornecedor", "rescindiu", "estornou", "adiou".
Memória é texto pessoal; regra extraída de um autor não generaliza sozinha.

**Regra:** vocabulário de detecção se valida contra dados que não são seus. É o
mesmo motivo do dataset existir com anotação humana cega: `testes/avaliar.py`
tem gate de recall (0,80) na CI, porque falso negativo é contradição que ninguém
verá. Depois da expansão por radicais de conjugação: recall 0,85.

(Bônus da mesma rodada: parte dos pares veio com `tipo: "fato"`, que não existe
no vocabulário, e o funil descartou tudo silenciosamente. Validador de dataset
agora trava tipo fora da spec. Vocabulário fechado só protege se alguém conferir.)
