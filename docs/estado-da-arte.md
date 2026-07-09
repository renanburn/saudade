# Por que assim: o estado da arte, com fonte

Cada escolha de desenho da saudade existe porque outra coisa quebrou antes.
Este documento junta o que já foi tentado, o que quebrou nelas, e o que a
saudade faz diferente. Nenhum número aqui é estimativa: são achados
publicados ou documentados pelos próprios projetos.

## Escrita deliberada, não extração automática

**O que os outros fazem.** O padrão do setor é extração automática: você
conversa, um LLM lê a conversa depois e decide o que virou memória. É como o
ChatGPT funciona e é o desenho do Mem0, que publica um pipeline onde o
próprio LLM decide `ADD`, `UPDATE`, `DELETE` ou `NOOP` pra cada pedaço extraído.

**O que quebra.** Extração automática significa que a máquina decide sozinha
o que é fato e o que descarta, sem ninguém validando no momento. A OpenAI
documenta que memórias podem ser alucinadas pro store (o sistema grava algo
que não foi dito), e admite que o sistema legado de memória tinha entradas
que envelheciam e se contradiziam sem ninguém arrumar. Tem outro risco: a
tool `bio` do ChatGPT pode ser acionada sem consentimento via prompt
injection indireta, ou seja, um texto malicioso que o usuário nem escreveu
pode fazer o sistema gravar memória falsa. Em 2026 a própria OpenAI está
trocando as memórias discretas por um resumo rolante automático, o que
é uma admissão de que o modelo anterior não estava dando certo.

**O que a saudade faz.** Escrita é sempre deliberada: alguém (humano ou
agente, mas em sessão real, decidindo naquele momento) grava um `add` com
tipo e texto explícitos. Não tem etapa de "o LLM decide depois o que
lembrar". Se ninguém mandou gravar, não foi gravado. Isso corta o risco de
alucinação no armazenamento, mas empurra a responsabilidade pra quem
escreve: ver a limitação honesta no fim deste documento.

## Invalidação bi-temporal, não deleção

**O que os outros fazem.** Zep e seu motor Graphiti usam um grafo de
conhecimento temporal: cada fato tem uma janela de validade, e fatos que
deixam de valer são invalidados (marcados com uma data de fim), não
apagados. É desse desenho que a saudade copia a lógica de invalidação.

**O que quebra.** A escrita nesses sistemas segue sendo extração automática
por LLM: o pipeline lê a conversa e decide o que virou nó no grafo, e o
próprio projeto documenta falha de ingestão quando roda com modelos mais
fracos. A estrutura de invalidação é boa, a forma de alimentar ela é o ponto
frágil.

**O que a saudade faz.** Pega a mecânica de invalidação do Graphiti (nunca
apaga, marca como morto e registra o porquê) mas aplica em cima de escrita
deliberada, não extração. `supersede` marca um fato como morto com motivo
explícito. `resolvido` dá baixa numa pendência ou bloqueio sem apagar o
registro de que ela existiu. A tabela de `relations` também tem
`valid_from` e `invalidated_at`: uma aresta pode ser invalidada e depois
reafirmada, sem perder o histórico de que ela já existiu, morreu, e voltou.

## Projeção por recência, sem carregar tudo

**O que os outros fazem.** A tentação óbvia é jogar o histórico inteiro no
contexto a cada conversa. Quanto mais sofisticado o sistema, mais ele tenta
resumir ou compactar automaticamente pra caber.

**O que quebra.** Anthropic documenta "context rot": a precisão de
recuperação cai conforme o contexto cresce, e isso vale pra todos os
modelos testados, não é peculiaridade de um provedor. Sumarização frequente
no momento do recall piora ainda mais: o estudo longitudinal de segurança
(arXiv 2605.17830, maio de 2026) aponta sumarização frequente como um dos
mecanismos que elevam a taxa de violação, porque fatos correlatos acabam
mesclados de um jeito que perde a distinção entre o que ainda vale e o que
já foi corrigido.

**O que a saudade faz.** O comando `estado` gera uma projeção determinística
enviesada por recência: bloqueios e pendências dos últimos 30 dias, decisões
e mudanças dos últimos 7, sem tocar no que é mais velho que isso (a não ser
que você mude a janela). Não é resumo de LLM, é filtro por data e por evento
(morto ou baixado não aparece). É essa projeção, e só ela, que entra no
prompt da IA. O log inteiro continua no banco pra busca e auditoria, mas
nunca é despejado inteiro em contexto nenhum.

## Sem embeddings, sem índice semântico como fonte

**O que os outros fazem.** A maioria dos sistemas de memória usa retrieval
semântico: embeddings, busca por similaridade vetorial, às vezes um grafo de
conhecimento construído em cima disso.

**O que quebra.** Dois achados batem na mesma direção. O primeiro, de
segurança: o estudo longitudinal (arXiv 2605.17830) mede que retrieval
semântico amplo com pouca restrição de recência produz taxa de violação
induzida por memória de 0,3 a 0,5, contra 0,1 a 0,2 em sistemas enviesados
por recência. Busca semântica ampla traz de volta informação desatualizada
junto com a relevante, e o sistema não tem como saber qual delas venceu. O
segundo, de arquitetura: os papers PROJECTMEM e ESAA-Conversational (2026)
defendem log de eventos tipados com projeção determinística por cima, e o
ESAA crava que índice semântico só pode ser uma projeção derivada do log,
nunca a fonte de verdade. Se o índice semântico é a fonte, você perde a
distinção entre fato vivo e fato morto no momento em que os dois têm
embedding parecido.

**O que a saudade faz.** Busca é FTS5 (full-text, BM25), não vetorial, e ela
sempre sabe distinguir vivo de morto porque isso vem do log estruturado, não
do texto: `buscar --vigente` esconde o que foi superado ou baixado, porque
o sistema consulta a tabela de eventos, não a similaridade de texto. Fonte
de verdade é sempre a tabela `observations` append-only. Qualquer índice
(FTS, projeção de estado, síntese de compactação) é derivado, nunca é onde
o fato mora.

## Benchmarks não decidem isto

**O que os outros fazem.** Cada projeto de memória publica um número no
LoCoMo (o benchmark mais citado da área) e usa isso como prova de qualidade.

**O que quebra.** Uma auditoria encontrou 99 erros que corrompem o score nas
1.540 perguntas do LoCoMo (6,4% delas), o que baixa o teto real de score
possível pra cerca de 93,6%. O juiz LLM padrão usado nesse benchmark aceitou
62,81% de respostas propositalmente erradas, só porque estavam no tema
certo. Mem0 e Zep publicaram scores contraditórios um do outro, medindo a
mesma coisa. E no MemoryBench, que testa em cenário dinâmico, nenhum sistema
de memória avançado bateu consistentemente RAG simples. Some a isso um dado
mais direto ainda: o próprio paper do Mem0 mostra que o baseline de contexto
completo (jogar tudo no prompt, sem memória nenhuma) tira J=72,90% no
LoCoMo, contra 66,88% do Mem0. A variante de grafo do Mem0 não ajuda em
perguntas multi-hop. E o resultado mais duro veio da Letta (ex-MemGPT): um
agente simples, só com ferramentas de sistema de arquivo, rodando GPT-4o
mini, tira 74,0% no LoCoMo e bate o melhor resultado do Mem0 (68,5%).
Arquitetura sofisticada perdeu pra filesystem simples.

**O que a saudade faz.** Não existe number a perseguir aqui. A saudade é
mais perto do desenho da Letta (armazenamento simples, tipado, auditável)
do que do desenho do Mem0 (pipeline de extração e grafo automático). Isso
não é escolha por benchmark, é escolha porque o benchmark mais citado da
área está com o teto quebrado e o juiz automático aceita resposta errada em
mais de 60% dos casos. Decisão de desenho aqui vem de onde o campo mostrou
falha estrutural (extração alucina, grafo automático não ajuda em
multi-hop, sumarização mescla fato morto com vivo), não de qual sistema
tirou nota mais alta num teste que a própria comunidade já provou furado.

## A memory tool da Anthropic como referência de arquitetura

A memory tool da Anthropic é baseada em arquivos, com escrita deliberada e
leitura just-in-time: o agente decide quando escrever e quando ler, não tem
pipeline automático rodando por trás. É a mesma filosofia da saudade, num
nível mais simples (arquivo puro, sem tipos nem invalidação bi-temporal). A
saudade pega esse princípio de deliberação e soma a mecânica de invalidação
do Graphiti, num banco que ainda cabe na cabeça.

## A limitação honesta

Escrita deliberada exige disciplina. Se ninguém escreve o fato, não há
memória. Não tem processo de fundo recuperando o que você esqueceu de
gravar, não tem LLM varrendo a conversa depois pra pescar o que passou
batido. Isso é o oposto do risco do Mem0 e do ChatGPT (memória que aparece
sozinha e pode estar errada), mas troca esse risco por outro: memória que
não aparece porque ninguém parou pra escrever.

É custo escolhido, não acidente de desenho. Entre "a IA pode inventar que
você disse algo que não disse" e "a IA não vai lembrar de algo que você
esqueceu de anotar", o segundo erra pra falta, não pra invenção. Falta se
percebe (a pendência não está lá, você nota). Invenção não se percebe até
virar decisão errada tomada em cima de fato que nunca existiu.
