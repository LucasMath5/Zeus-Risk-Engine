# Analytics básicos

## Objetivo e fronteiras

A Fase 6 transforma preços validados e alinhados em medidas descritivas reproduzíveis.
O módulo recebe objetos de domínio, executa funções puras e devolve resultados
imutáveis. Ele não lê arquivos, não acessa cache ou rede e não importa PySide6.

Estão incluídos retornos, retorno de carteira, momentos, volatilidade, covariância,
correlação, trajetória acumulada, drawdown, maximum drawdown e concentração por HHI.
VaR e Expected Shortfall permanecem fora desta fase.

## Convenção numérica

Entradas e resultados quantitativos usam `Decimal`. Cada cálculo abre um contexto local
com 34 dígitos de precisão e arredondamento `ROUND_HALF_EVEN`, equivalente à precisão
decimal128. O contexto global do processo não é alterado.

Essa escolha evita introduzir representação binária de `float` no domínio e torna a
política numérica explícita. Funções transcendentais como `ln`, `exp` e `sqrt` ainda são
aproximações na precisão configurada. Testes dessas operações usam tolerância absoluta
de `1e-32`; identidades decimais exatas são comparadas diretamente.

## Retornos por ativo

Para preços positivos consecutivos `P_(t-1)` e `P_t`, o retorno simples é:

```text
r_t = P_t / P_(t-1) - 1
```

Ele representa a variação percentual do período. Como os preços são estritamente
positivos, `r_t > -1`.

O retorno logarítmico é:

```text
l_t = ln(P_t / P_(t-1))
```

Retornos log são aditivos no tempo:

```text
Σ l_t = ln(P_final / P_inicial)
```

Cada retorno recebe a data final do intervalo. Portanto, `n` preços produzem `n - 1`
retornos. Menos de dois preços gera `INSUFFICIENT_PRICE_OBSERVATIONS`.

`calculate_return_table` exige uma tabela completa. Se o alinhamento por união contém
`None`, o cálculo gera `MISSING_ALIGNED_PRICE`; não remove datas e não preenche valores.
O usuário deve escolher interseção antes do cálculo ou resolver a política de ausência
em uma etapa futura explícita.

## Retorno de carteira

Os pesos líquidos são calculados sobre a fotografia de posições:

```text
w_i = V_i / Σ V_i
```

Para retornos simples dos ativos:

```text
r_(p,t) = Σ w_i r_(i,t)
```

Os mesmos pesos são reaplicados em todos os períodos. Essa é uma convenção de pesos
constantes, equivalente a rebalancear a carteira para os pesos iniciais a cada período;
não representa uma estratégia buy-and-hold.

Para entradas logarítmicas, somar diretamente `Σ w_i l_i` não produz, em geral, o
retorno log exato da carteira. A implementação reconstrói os retornos simples:

```text
r_(i,t) = exp(l_(i,t)) - 1
r_(p,t) = Σ w_i r_(i,t)
l_(p,t) = ln(1 + r_(p,t))
```

Posições vendidas preservam pesos negativos. Uma carteira de valor líquido zero não
possui pesos líquidos. Um período alavancado com `1 + r_(p,t) <= 0` não possui riqueza
positiva nem retorno log definido e gera `NON_POSITIVE_PORTFOLIO_GROWTH`.

Todos os ativos da tabela devem corresponder exatamente às posições selecionadas e
pertencer a uma única moeda. Não há conversão cambial implícita.

## Média, variância e volatilidade

Para `n` retornos, a média aritmética é:

```text
r̄ = (1 / n) Σ r_t
```

O estimador amostral, padrão do projeto, usa `n - 1`:

```text
s² = Σ (r_t - r̄)² / (n - 1)
s  = sqrt(s²)
```

Ele exige pelo menos duas observações. A alternativa populacional usa:

```text
σ² = Σ (r_t - r̄)² / n
σ  = sqrt(σ²)
```

O resultado registra `VarianceEstimator.SAMPLE` ou `POPULATION`. A volatilidade diária
é anualizada pela raiz do tempo:

```text
σ_anual = σ_diária × sqrt(A)
```

`A` é um `Decimal` positivo registrado no resultado e vale 252 por padrão. Isso é uma
convenção de escala, não um calendário de negociação nem uma afirmação de que retornos
são independentes e identicamente distribuídos. A média não é anualizada nesta fase.

## Covariância e correlação

Para séries alinhadas `x` e `y`, a covariância usa o mesmo estimador escolhido:

```text
cov_amostral(x,y) = Σ (x_t - x̄)(y_t - ȳ) / (n - 1)
cov_população(x,y) = Σ (x_t - x̄)(y_t - ȳ) / n
```

A correlação é:

```text
corr(x,y) = cov(x,y) / sqrt(var(x) × var(y))
```

As matrizes preservam a ordem das chaves, são quadradas e simétricas. A diagonal da
covariância é não negativa; a diagonal da correlação é 1. Uma série constante tem
variância zero: sua covariância ainda é válida, mas sua correlação é indefinida e gera
`ZERO_RETURN_VARIANCE` em vez de `NaN`.

## Trajetória acumulada e drawdown

A trajetória começa com índice de riqueza `W_0 = 1`. Para retorno simples:

```text
W_t = W_(t-1) × (1 + r_t)
```

Para retorno logarítmico:

```text
W_t = W_(t-1) × exp(l_t)
```

O retorno acumulado e o drawdown são:

```text
R_acum,t = W_t - 1
D_t = W_t / max(W_0, ..., W_t) - 1
```

`D_t` pertence a `[-1, 0]`. O resultado apresenta maximum drawdown como magnitude
positiva:

```text
MDD = max(-D_t)
```

Também registra a data do pico associado, o primeiro vale mais profundo encontrado e
a primeira recuperação posterior que alcança novamente o nível do pico. Se não houver
recuperação no período, `recovery_date` é `None`.

## Concentração

A concentração usa pesos brutos, não pesos líquidos assinados:

```text
g_i = |V_i| / Σ |V_i|
HHI = Σ g_i²
N_efetivo = 1 / HHI
```

Assim, `0 < HHI <= 1` e `N_efetivo >= 1`. Uma única posição tem HHI 1; quatro posições
iguais têm HHI 0,25 e número efetivo 4. Usar pesos líquidos em carteira long/short
poderia produzir HHI acima de 1 e uma interpretação enganosa, por isso não é permitido
por esse contrato.

## Exemplo manual

Considere os preços:

```text
100 → 110 → 99 → 108,9
```

Os retornos simples são:

```text
0,10; -0,10; 0,10
```

Logo:

```text
média amostral = 1 / 30 ≈ 0,0333333
variância amostral = 1 / 75 ≈ 0,0133333
riqueza = 1,10; 0,99; 1,089
maximum drawdown = 10%
pico = segundo preço; vale = terceiro preço; sem recuperação até o quarto
```

Esse conjunto está preservado em
[`tests/regression/test_basic_analytics_reference.py`](../../tests/regression/test_basic_analytics_reference.py).

## Uso programático

```python
from decimal import Decimal
from pathlib import Path

from zeus_risk.core.analytics import (
    calculate_descriptive_statistics,
    calculate_drawdown,
    calculate_return_table,
)
from zeus_risk.domain import ReturnMethod
from zeus_risk.market_data import (
    AlignmentPolicy,
    CsvMarketDataProvider,
    align_price_series,
)

market_data = CsvMarketDataProvider(Path("assets/samples/market_prices.csv")).load()
prices = align_price_series(market_data.data.series, AlignmentPolicy.INTERSECTION)
returns = calculate_return_table(prices, ReturnMethod.SIMPLE)
first_series = returns.series(returns.keys[0])

statistics = calculate_descriptive_statistics(
    first_series,
    annualization_factor=Decimal("252"),
)
drawdown = calculate_drawdown(first_series)

print(statistics.mean)
print(statistics.annualized_volatility)
print(drawdown.maximum_drawdown)
```

## Contratos e falhas

Resultados são representados por `ReturnSeries`, `ReturnTable`,
`DescriptiveStatistics`, `StatisticMatrix`, `DrawdownResult` e
`ConcentrationResult`. Eles preservam método, frequência, estimador, amostra ou pesos
aplicáveis e rejeitam valores não finitos.

Falhas operacionais usam `AnalyticsError` com `ValidationIssue` de código estável.
Entradas incapazes de formar um objeto de resultado nunca retornam `NaN` ou infinito
como sucesso.

## Limitações atuais

- somente frequência diária vinda dos contratos de mercado atuais;
- pesos de carteira são constantes e baseados nos preços da fotografia de posições;
- sem estratégia buy-and-hold, custos, fluxos de caixa, dividendos ou rebalanceamento
  configurável;
- sem conversão cambial ou agregação multimoeda;
- sem política quantitativa para `None`, interpolação ou calendário de negociação;
- sem exposições agregadas por setor/classe/moeda nesta entrega;
- sem janelas móveis, downside deviation, beta ou outros estimadores robustos;
- sem VaR, Expected Shortfall, backtesting ou inferência estatística;
- sem comandos CLI ou interface gráfica para analytics.

Essas limitações são deliberadas para que a Fase 7 possa introduzir VaR histórico
sobre uma base pequena, verificável e documentada.
