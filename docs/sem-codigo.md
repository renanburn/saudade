# saudade sem código: só com um arquivo de texto (ou Obsidian)

A saudade é um script Python com SQLite por baixo. Mas o script não é a ideia.
A ideia são três regras, e as três rodam num arquivo `.md` qualquer, sem
instalar nada:

1. Um fato por linha, com data.
2. Nunca apague. Marque o que morreu, dizendo por quê.
3. O que a IA lê todo dia é uma projeção do log, não o log inteiro.

Se você não quer rodar Python, abre uma nota no Obsidian e segue este guia.
Funciona igual. Migra pro banco depois, se e quando fizer sentido.

## O arquivo

Cria uma nota, `caderneta.md`. Cada linha é um fato, neste formato:

```
- [2026-07-09 14:00] decisao :: texto do fato (#42)
```

O `#42` é o id. Manual, incremental, você mesmo numera: olha a última linha
gravada, soma 1. Não tem trigger nem autoincrement, é você contando.

Tipos que valem a pena ter (os mesmos da saudade):

- `decisao`: algo foi resolvido
- `pendencia`: ficou em aberto, com dono
- `bloqueio`: não dá pra avançar até resolver outra coisa
- `experimento`: testou, ainda não decidiu
- `mudanca`: alteração estrutural concreta
- `observacao`: fato relevante, sem ação

## Baixa e morte são coisas diferentes

Uma `pendencia` ou um `bloqueio` que foi cumprido leva **baixa**. O fato
continua vivo no sentido de que ele aconteceu, só marca que já foi resolvido:

```
- [2026-07-10 09:00] resolvido :: #42 · wizard corrigido e testado
```

Um fato que **deixou de ser verdade** (você decidiu diferente, a premissa
caiu, foi erro) leva **supersede**. Isso é diferente de baixa: baixa fecha
tarefa, supersede mata fato. Quando você gravar o supersede, risca a linha
antiga com `~~tachado~~`, sem apagar nada:

```
- [2026-07-11 16:00] supersede :: #42 · decidiu manter o wizard antigo, motivo mudou
```

E a linha original vira:

```
- ~~[2026-07-09 14:00] decisao :: texto do fato (#42)~~
```

No Obsidian o tachado renderiza riscado e continua legível. É a presença da
ausência: você vê que existiu, vê que morreu, vê o porquê. Isso é o oposto de
deletar. Deletar apaga a evidência de que você já pensou diferente. Riscar
prova.

## O estado: a projeção manual

No topo do arquivo (ou numa nota separada, tipo `Estado.md`), você mantém uma
seção que reescreve por leitura das linhas não riscadas. Isso é a projeção:
o que vale agora, sem o histórico morto.

```markdown
## Estado (atualizado 2026-07-11)

**Pendências abertas:**
- nenhuma

**Decisões vigentes:**
- mantém o wizard antigo (#43, supera #42)

**Bloqueios:**
- nenhum
```

Você reescreve essa seção à mão, olhando o log de baixo pra cima, pegando só
o que não tem tachado e não levou baixa. Trabalhoso, sim. É o preço de não
ter código fazendo a projeção por você.

## Regras práticas

- **Um fato por linha.** Se a linha tem "e" no meio ligando dois eventos
  diferentes, são duas linhas. Fato empilhado não dá pra superar sozinho:
  você mata os dois ou não mata nenhum.
- **Data sempre.** Sem data você não sabe o que é recente e o que é velho, e
  a projeção por recência (que é o que faz a IA não afogar em contexto) fica
  impossível.
- **Nunca deletar linha.** Nem a que ficou feia, nem a que virou vergonha.
  Risca. A memória que esconde erro passado é pior que memória nenhuma:
  ela repete o erro porque ninguém lembra que ele já foi cometido.
- **A IA recebe só a seção de estado, nunca o arquivo inteiro.** Cola a
  seção `## Estado` no prompt. O log completo fica na nota, pra você
  auditar quando precisar, mas não entra em todo prompt. Isso é o que evita
  o "context rot": jogar o arquivo inteiro numa IA a cada conversa faz a
  precisão de recuperação cair conforme o histórico cresce.

## Exemplo completo

Um `caderneta.md` com dez linhas, mostrando a cadeia inteira: decisão
gravada, decisão superada (riscada, com a linha de supersede apontando o
motivo), e o estado no topo refletindo só o que sobrou vivo.

```markdown
## Estado (atualizado 2026-07-11 16:30)

**Decisões vigentes:**
- mantém o wizard antigo de onboarding (#43)

**Pendências abertas:**
- revisar copy da tela de boas-vindas (#45)

**Bloqueios:**
- nenhum

---

## Log

- [2026-07-08 10:00] mudanca :: subiu a v2 do onboarding pra produção (#40)
- [2026-07-08 11:20] observacao :: taxa de conclusão caiu de 61% pra 44% na v2 (#41)
- ~~[2026-07-09 14:00] decisao :: troca o wizard antigo pelo novo de vez, v2 vira padrão (#42)~~
- [2026-07-09 15:10] pendencia :: escrever copy nova da tela de boas-vindas pro wizard v2 (#44)
- [2026-07-11 09:00] supersede :: #42 · queda de 17 pontos na conclusão não compensa, volta o antigo enquanto arruma a v2 (#43)
- [2026-07-11 09:05] decisao :: mantém o wizard antigo de onboarding até a v2 recuperar a taxa (#43)
- [2026-07-11 09:10] supersede :: #44 · pendência era da copy do wizard v2, que saiu de produção (#46)
- [2026-07-11 16:00] pendencia :: revisar copy da tela de boas-vindas, agora pro wizard antigo mesmo (#45)
- [2026-07-11 16:20] observacao :: taxa de conclusão do wizard antigo voltou a 60% em 5 dias (#47)
```

Repara na mecânica: `#42` foi decidido, depois superado por `#43` (que
também é a nova decisão, na mesma sessão de trabalho: dois fatos, duas
linhas). `#44` foi pendência, também superada, porque o objeto dela
(a copy do wizard v2) deixou de existir quando o v2 saiu de produção. `#45`
é a pendência nova, equivalente na intenção mas sobre o objeto certo. O
estado no topo só mostra `#43` e `#45`: tudo que foi riscado ou resolvido
some da projeção, mas continua no log pra quem quiser auditar por quê.

## Quando migrar pro SQLite

Migra quando:

- o arquivo passar de algumas centenas de linhas e ficar difícil de
  reescrever o `## Estado` à mão sem esquecer algo,
- ou você quiser busca (achar todo fato que menciona "Aurora" sem abrir o
  arquivo e dar Ctrl-F visualmente linha por linha),
- ou mais de uma pessoa (ou agente) grava ao mesmo tempo e arquivo texto
  vira ponto de conflito de edição.

O formato não muda: `[data] tipo :: texto`, id incremental, supersede e
resolvido continuam funcionando do mesmo jeito. A migração é mecânica, quase
um script de dez linhas: lê cada linha do markdown, faz o parse de data, tipo
e texto, insere numa tabela `observations`. É literalmente o que o
`bin/saudade` faz por baixo. Você não perde nada trocando de camada, porque
a lógica sempre foi a das três regras, não do banco.
