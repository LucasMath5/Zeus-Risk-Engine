# Expected Shortfall histórico

## Escopo

A Fase 8 calcula Expected Shortfall (ES/CVaR) histórico relativo sobre o mesmo
resultado de VaR da Fase 7. O cálculo recebe uma `ReturnSeries` diária e uma
`HistoricalVaRConfiguration`, produz o VaR e deriva sua cauda sem selecionar outra
janela ou reconstruir convenções.

O core permanece puro: não lê arquivos, não acessa provider, cache ou rede, não
converte moedas e não importa PySide6.

## Relação com o VaR

O VaR histórico ordena `n` perdas e usa nearest-rank:

```text
k = ceil(confidence_level * n)
quantile_loss = L_(k)
VaR = max(quantile_loss, 0)
```

com `L_(1) <= ... <= L_(n)`. O Expected Shortfall usa exatamente os ranks
estritamente posteriores ao rank do VaR:

```text
tail = (L_(k+1), ..., L_(n))
tail_count = n - k
tail_mean_loss = sum(tail) / tail_count
ES = max(tail_mean_loss, 0)
```

A validação mínima da Fase 7,
`n >= ceil(1 / (1 - confidence_level))`, garante `tail_count >= 1`. O motor não
reduz a confiança nem inventa observações quando a série é insuficiente.

## Empates no limiar

A cauda é definida por rank, não pelas comparações `loss > quantile_loss` ou
`loss >= quantile_loss`. Perdas empatadas são ordenadas pela data final e depois
pela data inicial do cenário. Isso preserva:

- tamanho de cauda fixo para a mesma configuração;
- seleção determinística;
- média inalterada entre valores empatados;
- amostra de cauda auditável.

Quando um empate atravessa o rank `k`, parte das observações empatadas pode ficar no
limiar e parte na cauda. Expandir a cauda para todos os empates alteraria o peso
empírico configurado.

## Reconciliação com o VaR

Todo valor da cauda é maior ou igual a `quantile_loss`. Portanto:

```text
tail_mean_loss >= quantile_loss
max(tail_mean_loss, 0) >= max(quantile_loss, 0)
ES >= VaR
```

O resultado valida essa propriedade novamente. Se a média bruta da cauda representar
ganho, ela permanece disponível em `tail_mean_loss`, enquanto
`expected_shortfall` recebe piso em zero.

## Exemplo manual

Retornos simples:

```text
retornos:  0.02, -0.01, -0.04,  0.03, -0.10
perdas:   -0.02,  0.01,  0.04, -0.03,  0.10
ordenadas:-0.03, -0.02,  0.01,  0.04,  0.10
```

Para confiança de 80% e janela 5:

```text
k = ceil(0.80 * 5) = 4
VaR = L_(4) = 0.04
cauda = (L_(5)) = (0.10)
ES = 0.10
```

Nesse exemplo, VaR é 4% e Expected Shortfall é 10%. O ES descreve a média da cauda
empírica definida; não representa perda máxima possível nem garantia futura.

## Uso pelo código

```python
from decimal import Decimal

from zeus_risk.core.risk import calculate_historical_expected_shortfall
from zeus_risk.domain import HistoricalVaRConfiguration

configuration = HistoricalVaRConfiguration(
    confidence_level=Decimal("0.95"),
    horizon_days=1,
    window=252,
)
result = calculate_historical_expected_shortfall(return_series, configuration)

print(result.historical_var.value_at_risk)
print(result.expected_shortfall)
print(result.tail_count)
```

O chamador deve fornecer `return_series` pelo pipeline validado de preços e
retornos.

## Resultado estruturado

`HistoricalExpectedShortfallResult` registra:

- o `HistoricalVaRResult` completo e efetivamente usado;
- perdas da cauda em ordem crescente de severidade;
- média bruta da cauda;
- ES relativo não negativo;
- quantidade e intervalo de datas da cauda por propriedades derivadas.

Configuração, chave, método de retorno, frequência, unidade, convenção, janela e
amostra completa permanecem disponíveis no resultado de VaR associado.

## Falhas explícitas

| Código | Situação |
|---|---|
| `EMPTY_EXPECTED_SHORTFALL_TAIL` | não existe rank além do VaR |
| `INVALID_EXPECTED_SHORTFALL_VAR_RESULT` | resultado não contém um VaR validado |
| `INVALID_EXPECTED_SHORTFALL_TAIL` | cauda ausente ou com tipo inválido |
| `EXPECTED_SHORTFALL_TAIL_MISMATCH` | cauda não corresponde aos ranks após o VaR |
| `EXPECTED_SHORTFALL_MEAN_MISMATCH` | média não reconcilia com a cauda |
| `EXPECTED_SHORTFALL_VALUE_MISMATCH` | ES não reconcilia com a média e o piso |
| `EXPECTED_SHORTFALL_BELOW_VAR` | ES é inferior ao VaR associado |

Falhas de confiança, horizonte, janela, série ou amostra continuam usando os códigos
estruturados do VaR histórico.

## Limitações

- somente séries diárias completas e previamente validadas;
- cauda empírica por ranks, sem interpolação ou peso fracionário;
- cenários móveis sobrepostos e igualmente ponderados;
- somente unidade relativa;
- sem conversão cambial ou agregação multimoeda;
- sem VaR paramétrico, EWMA, backtesting ou Monte Carlo;
- sem interface gráfica, persistência ou relatórios.

As decisões e alternativas estão registradas no
[ADR-005](../decisions/ADR-005-historical-expected-shortfall-conventions.md).
