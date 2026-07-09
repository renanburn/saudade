# Dataset de avaliação — detecção de contradição em memória de trabalho (pt-BR)

## O que é

Dataset inicial (v1) de 72 pares de fatos em português brasileiro, pra avaliar
sistemas de detecção de contradição em memória de trabalho tipo "saudade":
memória append-only onde cada fato novo pode reverter, complementar ou não
mexer num fato antigo.

Cada par tem um fato `antigo`, um fato `novo` (mesma entidade, datas
diferentes), o palpite de um classificador automático (`rotulo_maquina`) e um
espaço vazio pra anotação humana (`rotulo_humano`, sempre `null` nesta
versão).

O valor do dataset não está nos casos óbvios. Está nos 24 pares
`nao_contradiz` difíceis (tarefa concluída que parece reversão, detalhe que
parece mudança, objeto diferente disfarçado de mesmo assunto) e nos 12 pares
`parcial` (fato antigo com dois fatos empilhados, novo mata só um). É esse
conjunto que separa um detector de contradição bom de um "deletador"
ingênuo que apaga memória demais.

## Arquivos

- `pares.jsonl` — os 72 pares, um JSON por linha.
- `GUIA-ANOTACAO.md` — guia pro anotador humano preencher `rotulo_humano`.
- `gen_pares.py` — script que gerou `pares.jsonl` (fonte editável).
- `validar.py` — validador estrutural do dataset (rode depois de qualquer
  edição em `pares.jsonl` ou `gen_pares.py`).

## Composição

- 26 `contradiz` (24 do desenho original + 2 do lote de extras)
- 32 `nao_contradiz` (24 difíceis + 8 do lote de extras)
- 14 `parcial` (12 do desenho original + 2 do lote de extras)
- Total: 72 pares, distribuídos igualmente entre 6 domínios (12 cada):
  negocio, freela-criativo, estudio-musica, clinica-estetica, agencia,
  pessoal-projetos.
- Entities e nomes de empresa são fictícios. Nenhuma coincidência com
  empresas reais é intencional.
- Em pelo menos 10 dos pares `contradiz`, a reversão usa vocabulário
  totalmente diferente do fato antigo (ex: "decidiu negociar a saída da
  contrato" → "seguiu firme e assumiu a linha nova"). É o caso que detectores
  por similaridade de texto costumam errar, e é por isso que ele está aqui.

## Como citar / referenciar

Ao usar este dataset num experimento ou relatório, referencie como:

> Dataset de contradição em memória de trabalho pt-BR v1 (72 pares),
> `dataset-saudade/pares.jsonl`, criado em 2026-07-09 pro projeto saudade.

Se o dataset crescer ou ganhar rodadas de anotação, versionar como v2, v3
etc. e manter o histórico de mudanças aqui.

## Estado da anotação

**v1, recém-gerado. `rotulo_humano` está `null` em todas as 72 linhas.**
Nenhuma anotação humana foi feita ainda. Antes de usar este dataset pra medir
acurácia de um detector, é preciso:

1. Um anotador humano (ou mais de um, pra medir concordância) ler
   `GUIA-ANOTACAO.md` e preencher `rotulo_humano` em cada linha, **sem olhar
   `rotulo_maquina`** (single-blind, conforme o guia).
2. Depois de anotado, `rotulo_humano` vira o gabarito. `rotulo_maquina`
   deixa de ser referência e passa a ser o que está sendo avaliado.
3. Se houver mais de um anotador, calcular concordância (ex: Cohen's kappa)
   antes de consolidar o gabarito final.

Até que o passo 1 aconteça, este dataset serve só como conjunto de teste
estrutural (o `rotulo_maquina` é uma hipótese de trabalho, não um gabarito).

## Validação

Rode `python3 validar.py` depois de qualquer edição. Ele checa: 72 linhas,
JSON válido, distribuição de rótulos, ids únicos e sequenciais,
`rotulo_humano` sempre `null`, nenhum texto duplicado, e uma heurística de
diversidade de vocabulário nos pares `contradiz`.
