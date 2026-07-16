# ADR-005 — Convenções do Expected Shortfall histórico

- **Estado:** aceito
- **Data:** 2026-07-16
- **Decisor:** Lucas Silva
- **Escopo:** Fase 8 — Expected Shortfall histórico

## Contexto

O Expected Shortfall depende de como a cauda empírica é selecionada. Com quantis
discretos, incluir o rank do VaR, usar perdas estritamente maiores que o limiar ou
incluir todos os valores empatados produz tamanhos e médias diferentes.

O ADR-004 já define perdas, nearest-rank, horizonte, janela, piso em zero e unidade do
VaR histórico. A Fase 8 deve preservar essas decisões e garantir que ES e VaR sejam
calculados sobre a mesma amostra.

## Decisão

### Fonte da cauda

`calculate_historical_expected_shortfall` calcula primeiro um
`HistoricalVaRResult` e o incorpora integralmente ao resultado de ES. Nenhuma
configuração, janela ou série paralela é criada.

### Definição por ranks

Para perdas ordenadas `L_(1) <= ... <= L_(n)` e rank do VaR
`k = ceil(c * n)`, a cauda contém `L_(k+1)` até `L_(n)`. O rank `k` não entra
na média. A quantidade efetiva é `n - k`.

A resolução mínima definida no ADR-004 garante pelo menos um rank na cauda. Uma cauda
vazia é falha estruturada.

### Empates

Empates usam ordenação estável por valor, data final e data inicial. A fronteira
continua sendo o rank, mesmo quando valores iguais aparecem dos dois lados. Assim, o
tamanho da cauda não muda por causa da multiplicidade de um valor.

### Média e piso

`tail_mean_loss` é a média aritmética igualmente ponderada da cauda. O valor
apresentado é `max(tail_mean_loss, 0)`; a média bruta permanece no resultado. Nenhum
arredondamento de exibição é aplicado.

### Reconciliação

Como toda perda da cauda é maior ou igual ao quantil, o contrato exige
`expected_shortfall >= value_at_risk`. Ambos usam a mesma unidade
`relative_return` e a mesma convenção `loss_equals_negative_return`.

## Consequências positivas

- ES e VaR não divergem em configuração ou amostra;
- o tamanho da cauda é determinístico;
- empates não aumentam arbitrariamente o peso da cauda;
- a propriedade `ES >= VaR` é verificável;
- média, observações e datas ficam auditáveis;
- a implementação reutiliza contratos existentes e não adiciona dependências.

## Consequências negativas e custos

- a fração empírica efetiva é `(n - k) / n`, que pode ser menor que `1 - c`;
- parte de um grupo empatado pode ficar fora da cauda;
- a escolha de desempate afeta quais datas empatadas aparecem, embora não altere a
  média;
- não existe ponderação fracionária na observação de fronteira;
- janelas mínimas podem produzir cauda com apenas uma observação.

## Alternativas consideradas

### Incluir o rank do VaR

Rejeitado porque produziria cauda `k ... n` e massa empírica maior que a região
estritamente posterior ao limiar de rank.

### Usar `loss > quantile_loss`

Rejeitado porque todos os valores podem estar empatados e gerar cauda vazia apesar de
existirem ranks posteriores.

### Usar `loss >= quantile_loss`

Rejeitado porque empates podem expandir a cauda de forma abrupta e dependente da massa
no limiar.

### Peso fracionário na fronteira

Adiado. Ele aproximaria exatamente a massa teórica `1 - c`, mas acrescentaria uma
convenção de interpolação e observações ponderadas que nearest-rank deliberadamente
evitou na Fase 7.

### Recalcular VaR dentro de um resultado independente

Rejeitado porque duplicaria configuração e amostra e permitiria resultados
incompatíveis.

## Regras verificáveis

- o resultado contém o VaR completo usado;
- a cauda contém exatamente os ranks `k+1 ... n`;
- empates são resolvidos cronologicamente;
- a cauda nunca é vazia para uma configuração válida;
- a média usa pesos iguais e contexto decimal de 34 dígitos;
- ES é finito, não negativo e não inferior ao VaR;
- unidade e convenção são herdadas do VaR;
- o core não importa arquivo, provider, cache ou Qt.

## Critério de reconsideração

Esta decisão deve ser revista quando forem introduzidos quantis interpolados, pesos
temporais, frequências além de diária, Expected Shortfall paramétrico, backtesting,
valor monetário ou exigência regulatória com definição específica de cauda.

## Relações

- [Expected Shortfall histórico](../concepts/historical-expected-shortfall.md)
- [Value at Risk histórico](../concepts/historical-var.md)
- [ADR-004 — Convenções do VaR histórico](ADR-004-historical-var-conventions.md)
- [Visão geral da arquitetura](../architecture/overview.md)
- [Glossário](../glossary.md)
