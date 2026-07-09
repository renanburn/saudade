# O incidente

Todo repo de infraestrutura tem um doc de arquitetura. Este tem um boletim de ocorrência. A saudade não nasceu de um paper: nasceu de uma semana em que a memória do meu próprio agente me deixou construir em cima de um fato morto, e do conserto ter quase apagado fatos vivos. Os dois atos importam.

Os ids abaixo são reais, do banco onde aconteceu.

## Ato 1: o fato que não sabia morrer

**2 de julho de 2026.** Gravei na memória de trabalho do meu agente:

> `#1198 [2026-07-02 12:07] mudanca :: um acerto antigo tinha ficado só no combinado verbal; decidi encerrar uma frente do negócio (...)`

Eu ia encerrar uma frente importante do negócio. Fato gravado, datado, correto naquele dia. (As citações deste doc preservam ids, datas e estrutura; o conteúdo de negócio foi descaracterizado de propósito, porque a caderneta é minha, mas as pessoas e empresas dela não assinaram este repo.)

**Entre 4 e 5 de julho**, o agente rodou quatro rodadas de planejamento pesado em cima disso. A premissa "essa fonte de renda vai acabar" virou urgência, a urgência virou desenho: um plano com datas, preços e metas; papéis divididos; um blueprint executável de 58 mil caracteres. Trabalho tecnicamente bom. Fundação podre.

**8 de julho.** Eu disse, numa frase solta no meio de outra conversa, que tinha voltado atrás. O agente gravou:

> `#1230 [2026-07-08 06:41] decisao :: voltou atrás: a frente FICA, e ganha um projeto novo em cima (...)`

E aqui está o problema inteiro deste repositório: **as duas linhas conviveram**. O log era append-only (bom), mas não tinha conceito de fato superado (fatal). Nenhuma estrutura marcava `#1198` como morto. Nenhum leitor sabia qual linha matava qual. O fato velho continuou alimentando projeções, resumos e contexto de sessões novas, com a mesma cara de verdade do fato novo.

Ninguém mentiu. Ninguém esqueceu de gravar. O sistema só não sabia esquecer.

O custo: quatro rodadas de conselho multi-agente, horas de trabalho meu e do agente, documentos inteiros no vault, tudo desenhado pra um cenário que já tinha sido revertido. Descoberto por acaso, porque eu corrigi numa mensagem. Se eu não tivesse mencionado, o plano seguia.

## O conserto

O diagnóstico coube numa frase: a tabela de fatos tinha `id`, `texto` e `data`, e **nenhum campo de validade**. Correção só podia ser gravada como mais um append, indistinguível de qualquer outro fato.

Entrou o evento `supersede`:

```
supersede :: #1198 · voltei atrás (#1230); a premissa de encerramento caiu
```

O `#1198` não foi apagado. Está lá até hoje, legível, com a data em que foi verdade e o evento que o matou. As projeções pararam de mostrá-lo no mesmo minuto. É isso que o nome do repo significa: a presença de uma ausência.

## Ato 2: o conserto que quase apagou a verdade

Construí em seguida um detector de contradição: filtro determinístico acha pares suspeitos (fato antigo vs fato novo com marca de reversão), um modelo julga, e sai um relatório com supersedes **propostos**.

Na primeira rodada real, ele achou o incidente sozinho: propôs matar `#1197`, `#1198` e `#1177` por causa do `#1230`, com confiança entre 0,85 e 0,95. Três minutos pra achar o que tinha me custado quatro rodadas.

E se eu tivesse aplicado as propostas automaticamente, **teria apagado fatos verdadeiros**.

Porque o `#1198` empilhava dois fatos numa linha só: *"o acerto ficou só no verbal"* (verdade até hoje) e *"decidi encerrar"* (morto). O `#1197` idem: um pedido novo de um parceiro (vivo) junto com a hipótese de encerramento (morta). Superar a linha inteira mataria o vivo junto com o morto. A máquina não tinha como saber. Só ler o texto completo revelou.

A solução foi cirúrgica e é a receita canônica pra fato duplo:

1. gravar cada metade como fato próprio, **retro-datado na data original**;
2. superar só a metade morta, apontando a causa (`#1230`);
3. superar a linha original apontando pros filhos: *"quebrada: empilhava fato vivo e fato morto"*.

Nada apagado. A linha do tempo não mente. E o log agora registra até o erro de modelagem: quem ler vê que houve um fato duplo, quando foi quebrado e por quê.

## As três cicatrizes que viraram regra

**Um fato por linha.** Não é estilo, é pré-condição de invalidação. Fato duplo não morre pela metade. O `saudade lint` avisa na entrada porque avisar depois é tarde.

**Confiança não é licença.** 0,95 do juiz e ainda assim errado no escopo. Por isso `saudade contradicoes` escreve relatório e para. A regra "a máquina propõe, o humano decide" não é filosofia de governança, é a diferença prática entre este repo e um deletador automático de memória.

**Supersede errado é pior que fato morto.** Fato morto visível você percebe e corrige. Memória boa apagada em silêncio, você só descobre quando precisa dela. Entre os dois riscos, a saudade escolhe sempre o que se enxerga.

## Por que publicar isto

Porque a peça mais útil de um sistema de memória não é o benchmark, é o modo de falha. Todo material de venda de memória pra IA mostra o recall bonito; nenhum mostra o dia em que o sistema deixou o dono planejar um trimestre em cima de um fato revertido. Foi exatamente esse dia que desenhou cada regra daqui.

Se você opera um agente com memória, a pergunta não é se isso vai acontecer contigo. É se você vai perceber quando acontecer.
