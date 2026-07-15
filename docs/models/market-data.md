# Dados de mercado locais

## Objetivo

A Fase 5 introduz um contrato offline, tipado e reproduzível para preços históricos.
O domínio conhece séries e metadados, mas não conhece CSV, caminhos de arquivos,
cache ou rede. O adapter CSV transforma uma fonte local nesses contratos e registra
problemas com códigos estáveis.

Esta fase não calcula retornos, volatilidade, correlação, drawdown ou risco. Esses
cálculos começam na Fase 6 e recebem apenas dados já validados e alinhados.

## Formato CSV

O provider usa o formato longo: cada linha representa um preço de uma série em uma
data.

```csv
ticker,date,price,currency
ZEUS_EQ1,2026-01-02,100.00,BRL
ZEUS_EQ1,2026-01-05,101.50,BRL
ZEUS_EQ2,2026-01-02,50.00,BRL
ZEUS_EQ2,2026-01-05,51.25,BRL
```

As quatro colunas são obrigatórias:

| Campo canônico | Aliases aceitos | Regra |
|---|---|---|
| `ticker` | `symbol`, `ativo`, `codigo` | texto não vazio, aparado e normalizado para maiúsculas |
| `date` | `data` | data de calendário ISO `YYYY-MM-DD` |
| `price` | `close`, `preco`, `fechamento` | `Decimal` finito e estritamente positivo, com ponto decimal |
| `currency` | `ccy`, `moeda` | código de três letras reconhecido pelo objeto `Currency` |

Cabeçalhos ignoram maiúsculas, acentos e separadores de palavras. Mais de uma coluna
mapeada para o mesmo campo é erro. Colunas desconhecidas são ignoradas com o aviso
`EXTRA_MARKET_DATA_COLUMNS_IGNORED`.

O arquivo deve ser UTF-8, com ou sem BOM. O delimitador pode ser vírgula, ponto e
vírgula, tab ou barra vertical; quando não é informado, o provider o detecta sobre uma
amostra limitada. Os limites padrão são 25 MiB e 250.000 linhas de dados.

O exemplo versionado está em
[`assets/samples/market_prices.csv`](../../assets/samples/market_prices.csv).

## Identidade e invariantes

`PriceSeriesKey` identifica uma série pelo par `(ticker, currency)`. A moeda integra a
chave porque o projeto ainda não converte valores para uma moeda-base. Um mesmo ticker
em moedas diferentes representa séries diferentes.

`PriceObservation` contém uma data sem horário e um preço positivo. `PriceSeries`
contém ao menos uma observação, tem frequência diária e exige datas únicas em ordem
estritamente crescente. O provider aceita linhas fora de ordem, ordena cada série e
emite `PRICE_ROWS_REORDERED`; duplicar ticker, moeda e data é sempre erro.

`MarketDataSet` reúne séries com chaves únicas e frequência uniforme. Seus totais e
intervalo devem reconciliar exatamente com `MarketDataMetadata`.

## Metadados e proveniência

O provider registra:

- identificador estável `csv-local` e caminho da fonte;
- frequência diária e instante de carga com timezone;
- SHA-256 dos bytes originais do arquivo;
- primeira e última data presentes;
- quantidade de séries, observações e linhas descartadas;
- política efetiva de preço ausente.

O hash identifica o conteúdo lido, não autentica seu autor e não substitui o arquivo
original. Alterar bytes, inclusive formatação, produz outra chave de cache.

## Valores ausentes

`CsvMarketDataOptions.missing_value_policy` exige uma decisão explícita:

- `MissingValuePolicy.ERROR` é o padrão e rejeita uma linha sem `price`;
- `MissingValuePolicy.DROP` descarta somente linhas cujo preço está ausente, emite
  `MISSING_PRICE_DROPPED` e incrementa `dropped_rows`.

Valores presentes, porém inválidos, como zero, negativo, `NaN`, infinito ou texto, não
são descartados por `DROP`: continuam sendo erros. Nenhum preço é interpolado,
carregado para frente ou substituído por zero.

## Alinhamento

`align_price_series` preserva a ordem das séries recebidas e cria uma tabela com datas
crescentes:

- `AlignmentPolicy.INTERSECTION` mantém apenas datas presentes em todas as séries e
  nunca produz `None`; a ausência de qualquer data comum gera `NO_COMMON_PRICE_DATES`;
- `AlignmentPolicy.UNION` mantém todas as datas presentes em pelo menos uma série e
  usa `None` onde uma série não possui observação.

As duas políticas são determinísticas e não preenchem lacunas. A política fica
registrada em `AlignedPriceTable` para que cálculos posteriores não precisem inferi-la.

## Cache JSON

`JsonMarketDataCache` persiste um `MarketDataLoadResult` já validado. A chave é o
SHA-256 da fonte e o nome segue
`market-data-v1-<sha256>.json`. O payload preserva schema, metadados, observações e
avisos. A gravação usa um arquivo temporário no mesmo diretório e substituição atômica.

A leitura reconstrói todos os objetos de domínio e reaplica suas invariantes. JSON
corrompido, schema incompatível, hash divergente ou conteúdo inválido gera
`MarketDataError`; ausência de uma entrada retorna `None`. O cache não baixa dados,
não decide expiração e não oculta `source_name`.

## Uso programático

```python
from pathlib import Path

from zeus_risk.market_data import (
    AlignmentPolicy,
    CsvMarketDataProvider,
    JsonMarketDataCache,
    align_price_series,
)

provider = CsvMarketDataProvider(Path("assets/samples/market_prices.csv"))
result = provider.load()

aligned = align_price_series(result.data.series, AlignmentPolicy.INTERSECTION)
cache = JsonMarketDataCache(Path(".cache/market-data"))
cache_path = cache.store(result)
restored = cache.load(result.data.metadata.content_hash)
```

`MarketDataProvider` é um `Protocol` pequeno com `provider_name` e `load()`. Assim, um
caso de uso futuro pode receber outro provider sem importar o adapter CSV.

## Falhas e diagnóstico

Uma carga bem-sucedida retorna `MarketDataLoadResult` e pode conter apenas avisos.
Quando não é possível construir um conjunto válido, `MarketDataError.problems` reúne
um ou mais `MarketDataIssue`, cada um com `ValidationIssue` e linha física opcional.
Os códigos, e não o texto humano, são o contrato recomendado para testes e tradução.

Erros independentes de várias linhas são acumulados na mesma tentativa. Falhas
estruturais, como arquivo ausente, encoding inválido, cabeçalho ausente ou limite
excedido, encerram a carga porque impedem interpretar as demais linhas com segurança.

## Limitações atuais

- somente frequência diária e preço de fechamento genérico;
- sem calendário de negociação, timezone por observação ou ajuste corporativo;
- sem formato largo, XLSX de preços, API externa ou atualização incremental;
- sem preenchimento estatístico, conversão cambial ou seleção automática de moeda;
- leitura síncrona e integral dos bytes, protegida pelos limites configuráveis;
- o cache é local e não substitui persistência de projetos ou histórico de execuções.

Essas fronteiras evitam misturar aquisição, limpeza implícita e cálculo quantitativo.
