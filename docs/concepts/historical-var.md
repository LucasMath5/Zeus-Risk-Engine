# Value at Risk histórico

## Escopo

A Fase 7 calcula Value at Risk (VaR) histórico relativo sobre uma `ReturnSeries`
diária já validada. O cálculo é puro: não lê arquivos, não consulta providers ou
cache, não converte moedas e não importa PySide6.

O resultado preserva a amostra efetiva de perdas, configuração, método de retorno,
unidade, convenção de sinal, rank do quantil e datas. Expected Shortfall permanece
fora desta fase.

## Configuração

`HistoricalVaRConfiguration` contém:

| Campo | Regra |
|---|---|
| `confidence_level` | `Decimal` finito, estritamente entre 0 e 1 |
| `horizon_days` | inteiro positivo; representa observações diárias consecutivas |
| `window` | quantidade positiva de cenários de horizonte na amostra final |
| `quantile_method` | `nearest_rank`, sem interpolação |

O método atual exige resolução mínima da cauda:

```text
window_min = ceil(1 / (1 - confidence_level))
```

Assim, 95% exige ao menos 20 cenários e 99% exige ao menos 100. A regra garante ao
menos uma observação além do rank do VaR. Ela não afirma que essa quantidade seja
estatisticamente adequada para qualquer uso; é somente o mínimo técnico aceito.

## Formação dos cenários

Para retorno simples diário `r_t` e horizonte `h`:

```text
R_(t,h) = product(1 + r_j) - 1
```

O produto cobre as `h` observações que terminam em `t`. Para retornos
logarítmicos:

```text
R_(t,h) = sum(r_j)
```

Os blocos são móveis e sobrepostos. Não é aplicada regra da raiz do tempo. Com
`n` retornos e horizonte `h`, existem `n - h + 1` cenários. Depois de formar
todos os cenários, o motor seleciona deterministicamente os `window` mais recentes.

`horizon_days` significa períodos de observação diária, não dias corridos. O motor
não inventa pregões ausentes nem um calendário de negociação.

## Convenção de perda e quantil

Cada cenário é transformado sem ambiguidade:

```text
loss = -horizon_return
```

Perda econômica tem sinal positivo; ganho tem sinal negativo. Para perdas ordenadas
`L_(1) <= ... <= L_(w)`, confiança `c` e janela `w`, nearest-rank usa:

```text
k = ceil(c * w)
quantile_loss = L_(k)
VaR = max(quantile_loss, 0)
```

Não há interpolação. O piso em zero evita apresentar um quantil de ganho como risco
negativo. O resultado mantém `quantile_loss` e `value_at_risk` separadamente para
que esse piso seja auditável.

Se a entrada usa retorno simples, o resultado está em unidades de retorno simples.
Se usa retorno logarítmico, permanece em unidades de log-retorno; não ocorre conversão
silenciosa.

## Exemplo manual

Considere cinco retornos simples de um dia:

```text
retornos:  0.02, -0.01, -0.04,  0.03, -0.10
perdas:   -0.02,  0.01,  0.04, -0.03,  0.10
ordenadas:-0.03, -0.02,  0.01,  0.04,  0.10
```

Para confiança de 80%, horizonte 1 e janela 5:

```text
k = ceil(0.80 * 5) = 4
quantile_loss = 0.04
VaR = 0.04
```

Sob essa amostra e convenção, o limiar histórico é uma perda relativa de 4%. Isso não
significa garantia, previsão causal nem perda máxima possível.

## Uso pelo código

```python
from decimal import Decimal

from zeus_risk.core.risk import calculate_historical_var
from zeus_risk.domain import HistoricalVaRConfiguration

configuration = HistoricalVaRConfiguration(
    confidence_level=Decimal("0.95"),
    horizon_days=1,
    window=252,
)
result = calculate_historical_var(return_series, configuration)

print(result.value_at_risk)
print(result.quantile_rank)
print(result.sample_start_date, result.sample_end_date)
```

O chamador deve fornecer `return_series` a partir do pipeline validado de preços e
retornos.

## Resultado estruturado

`HistoricalVaRResult` registra:

- chave, frequência e método da série;
- configuração completa;
- cenários de perda cronológicos com início, fim e valor;
- quantidade efetiva de cenários;
- rank e perda bruta do quantil;
- VaR relativo não negativo;
- data de referência e intervalo da amostra;
- `loss_equals_negative_return` como convenção;
- `relative_return` como unidade.

As invariantes do domínio reconciliam novamente janela, ordem das datas, rank, quantil,
piso do VaR e data de referência.

## Falhas explícitas

| Código | Situação |
|---|---|
| `INVALID_VAR_CONFIDENCE_LEVEL` | confiança fora do intervalo aberto (0, 1) |
| `INVALID_VAR_HORIZON` | horizonte não inteiro positivo |
| `INVALID_VAR_WINDOW` | janela não inteira positiva |
| `INVALID_VAR_QUANTILE_METHOD` | método diferente de nearest-rank |
| `INSUFFICIENT_VAR_TAIL_OBSERVATIONS` | janela não resolve a cauda da confiança |
| `INSUFFICIENT_HISTORICAL_OBSERVATIONS` | série não forma janela e horizonte pedidos |
| `INVALID_VAR_RETURN_SERIES` | fronteira recebeu objeto que não é `ReturnSeries` |
| `INVALID_VAR_CONFIGURATION` | fronteira recebeu configuração não validada |

Essas condições não retornam zero, `NaN` ou infinito como substitutos de sucesso.
Zero é resultado válido somente quando o quantil empírico é um ganho ou exatamente
zero e o piso documentado é aplicado.

## Limitações

- somente séries diárias completas e previamente validadas;
- cenários sobrepostos, sem ponderação temporal;
- somente nearest-rank;
- VaR relativo, sem conversão monetária;
- nenhuma conversão cambial ou agregação multimoeda;
- sem Expected Shortfall, VaR paramétrico, EWMA, backtesting ou Monte Carlo;
- sem testes de adequação da janela ao uso econômico;
- sem interface gráfica, persistência ou relatório.

As convenções e alternativas estão registradas no
[ADR-004](../decisions/ADR-004-historical-var-conventions.md).
