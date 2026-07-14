# Modelo de domínio de carteira

## Objetivo

Este documento descreve os modelos e cálculos da Fase 2. O escopo é deliberadamente
pequeno: representar instrumentos, posições e carteiras válidas, calcular valores de
mercado e normalizar pesos. Não há importação, séries históricas, conversão cambial ou
métrica de risco nesta fase.

As convenções numéricas são formalizadas no
[ADR-003](../decisions/ADR-003-decimal-and-portfolio-weights.md).

## Modelos

| Modelo | Responsabilidade | Invariantes principais |
|---|---|---|
| `Currency` | código da moeda do instrumento | três letras ASCII, normalizadas em maiúsculas |
| `AssetClass` | taxonomia inicial de instrumentos | valor pertencente ao enum suportado |
| `Instrument` | identidade e classificação | ticker não vazio, classe e moeda válidas |
| `Position` | quantidade e preço de um instrumento | `Decimal` finito, quantidade não zero, preço positivo |
| `Portfolio` | agregado imutável de posições | nome não vazio, tupla não vazia, sem ticker/moeda duplicado |
| `PortfolioValuation` | valores líquido e bruto por moeda | resultado estruturado, sem conversão implícita |
| `PositionWeight` | peso de uma posição | moeda, base, valor assinado e peso explícitos |
| `ValidationIssue` | problema estável e apresentável | severidade, código e mensagem válidos |

Os objetos usam dataclasses `frozen=True` e `slots=True`. A imutabilidade reduz mudanças
acidentais depois da validação e torna entradas de cálculo mais previsíveis. Ela não
substitui persistência nem representa segurança criptográfica.

## Normalização

- ticker: espaços externos removidos e texto convertido para maiúsculas;
- moeda: espaços externos removidos e código convertido para maiúsculas;
- setor: espaços externos removidos; texto vazio torna-se `None`;
- nome da carteira: espaços externos removidos;
- ordem das posições: preservada para rastreabilidade e apresentação;
- ordem das moedas agregadas: crescente por código.

Normalizar não significa tentar adivinhar o instrumento. A existência de `PETR4`, por
exemplo, será responsabilidade de dados de referência ou de mercado em fases futuras.

## Representação decimal

Valores devem ser construídos sem passar por `float`:

```python
from decimal import Decimal

quantity = Decimal("10.5")
price = Decimal("25.37")
```

Construir `Decimal(25.37)` preservaria o valor binário aproximado do `float`, não o texto
decimal pretendido. Por isso, o domínio aceita apenas instâncias de `Decimal` para
quantidade e preço.

Não há arredondamento automático. A quantidade de casas depende do instrumento e da
fonte; arredondar para duas casas nesta camada poderia perder informação.

## Valor de mercado

### Definição

O valor de mercado de uma posição é o produto entre quantidade assinada e preço:

```text
V_i = q_i × p_i
```

### Hipóteses

- preço e quantidade pertencem à mesma unidade do instrumento;
- o preço é válido na data de referência desejada;
- não existe multiplicador de contrato;
- não são aplicados juros acumulados, custos, impostos ou conversão cambial;
- quantidade negativa representa uma posição vendida.

### Exemplo simples

```text
PETR4: quantidade = 10, preço = BRL 25  → V = BRL 250
VALE3: quantidade =  5, preço = BRL 70  → V = BRL 350

Valor líquido = BRL 600
Valor bruto   = BRL 600
```

### Carteira long/short

Para posições na mesma moeda:

```text
N = Σ V_i
G = Σ |V_i|
```

Exemplo:

```text
LONG3  =  BRL 1.000
SHORT3 = -BRL   200

N =  1.000 - 200 = BRL   800
G = |1.000| + |-200| = BRL 1.200
```

`N` mede a exposição líquida na convenção simplificada da fase. `G` mede a magnitude
total das posições sem compensar comprado e vendido.

## Pesos

### Base líquida

```text
w_i(net) = V_i / N, para N ≠ 0
```

No exemplo long/short:

```text
w_LONG(net)  =  1.000 / 800 =  1,25
w_SHORT(net) =   -200 / 800 = -0,25
soma = 1,00
```

Um peso de 125% não é erro: ele indica que a posição comprada supera o patrimônio
líquido porque existe compensação vendida. Se `N = 0`, os pesos líquidos são
matematicamente indefinidos e o domínio gera `ZERO_NET_MARKET_VALUE`.

### Base bruta

```text
w_i(gross) = |V_i| / G
```

No mesmo exemplo:

```text
w_LONG(gross)  = 1.000 / 1.200 ≈ 0,833333
w_SHORT(gross) =   200 / 1.200 ≈ 0,166667
soma ≈ 1,00
```

Pesos brutos mostram a distribuição da magnitude da exposição, mas perdem o sinal da
direção. O resultado ainda inclui o valor de mercado assinado para preservar contexto.

## Moedas

Somar BRL 250 com USD 400 sem uma taxa e uma data de câmbio não produz uma medida
financeira válida. Portanto:

- `portfolio.valuations()` retorna um resultado separado para cada moeda;
- `portfolio.valuation(Currency("USD"))` seleciona uma moeda;
- `portfolio.market_value` só funciona diretamente em carteira de moeda única;
- pesos de carteira multimoeda exigem o argumento `currency`;
- nenhuma moeda-base é presumida.

A conversão futura deverá registrar par cambial, fonte, data, convenção e política para
dados ausentes.

## Duplicidades

Na Fase 2, a chave de posição é:

```text
(ticker normalizado, moeda)
```

Duas ocorrências da mesma chave geram `DUPLICATE_POSITION`. O mesmo ticker em moedas
diferentes é preservado, pois ticker isolado não é identificador universal. A chave
será ampliada quando mercado, book ou estratégia forem campos suportados.

## Validação e falhas

Entradas que violam invariantes geram `DomainValidationError`, contendo um ou mais
`ValidationIssue`. A exceção não substitui o problema estruturado; ela impede a criação
do objeto e transporta códigos que importadores e interface poderão traduzir.

Exemplos de códigos:

| Código | Significado |
|---|---|
| `EMPTY_TICKER` | ticker vazio após normalização |
| `INVALID_CURRENCY_CODE` | moeda fora do formato de três letras |
| `NON_FINITE_QUANTITY` | quantidade `NaN` ou infinita |
| `ZERO_QUANTITY` | posição sem exposição |
| `NON_POSITIVE_PRICE` | preço zero ou negativo |
| `DUPLICATE_POSITION` | ticker/moeda repetido na carteira |
| `CURRENCY_CONVERSION_REQUIRED` | tentativa de agregar moedas diferentes |
| `ZERO_NET_MARKET_VALUE` | peso líquido solicitado com denominador zero |

Na futura importação CSV, cada exceção poderá ser associada à linha original sem
encerrar a validação das demais linhas.

## Exemplo executável

```python
from decimal import Decimal

from zeus_risk.domain import AssetClass, Currency, Instrument, Portfolio, Position

brl = Currency("BRL")
petr4 = Instrument("PETR4", AssetClass.EQUITY, brl, sector="Energy")
vale3 = Instrument("VALE3", AssetClass.EQUITY, brl, sector="Materials")

portfolio = Portfolio(
    name="Brazil Equity",
    positions=(
        Position(petr4, quantity=Decimal("10"), price=Decimal("25")),
        Position(vale3, quantity=Decimal("5"), price=Decimal("70")),
    ),
)

assert portfolio.market_value == Decimal("600")
assert sum(weight.weight for weight in portfolio.weights()) == Decimal("1")
```

## Interpretação

- valor de mercado é uma fotografia das posições e preços fornecidos;
- valor líquido mede soma assinada, não risco;
- valor bruto mede tamanho de exposição, não perda possível;
- peso é relativo a uma base escolhida, não uma recomendação de alocação;
- nenhuma dessas medidas incorpora volatilidade, liquidez ou correlação.

## Limitações atuais

- não há multiplicadores de contrato ou lote;
- não há preço sujo/limpo, accrued interest ou duration;
- não há derivativos ou sensibilidades;
- não há conversão para moeda-base;
- não há dados temporais ou preço por data;
- não há agrupamento por setor ou classe;
- não há edição ou consolidação automática de duplicidades;
- não há importador; objetos são criados por código.

## Estratégia de testes

- exemplos manuais verificam valores líquido e bruto;
- posições compradas e vendidas verificam convenção de sinal;
- carteiras neutras verificam a rejeição apenas do peso líquido;
- carteiras multimoeda verificam a ausência de conversão implícita;
- casos parametrizados cobrem zero, negativos, `NaN`, infinito e tipos incorretos;
- imutabilidade é verificada para os principais objetos;
- somas de pesos periódicos usam tolerância decimal explícita de `1e-26`;
- toda a suíte executa sem PySide6 e sem chamadas externas.
