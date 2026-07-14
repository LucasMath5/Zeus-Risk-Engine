# Formato CSV de carteira

## Objetivo

Este documento define o contrato de importação CSV da Fase 3. O adapter transforma
texto externo em modelos validados da Fase 2 sem encerrar o processamento no primeiro
erro de linha.

O CSV é uma fronteira de infraestrutura. `Instrument`, `Position` e `Portfolio` não
conhecem caminhos, delimitadores, cabeçalhos ou encoding.

## Encoding

São aceitos:

- UTF-8;
- UTF-8 com BOM, usando `utf-8-sig` como padrão.

Não há fallback automático para Windows-1252 ou Latin-1. Um arquivo incompatível gera
`INVALID_FILE_ENCODING`. Essa escolha evita que bytes sejam decodificados em caracteres
incorretos sem aviso.

## Delimitadores

O importador aceita apenas:

| Delimitador | Representação |
|---|---|
| vírgula | `,` |
| ponto e vírgula | `;` |
| tab | `\t` |
| barra vertical | `|` |

Quando não for informado, o delimitador é detectado entre essas quatro opções. Se a
detecção não for conclusiva, a vírgula é usada; um cabeçalho incompatível falhará na
validação das colunas obrigatórias. O delimitador efetivo fica registrado em
`ImportResult`.

## Colunas

### Obrigatórias

| Campo canônico | Descrição | Exemplo |
|---|---|---|
| `ticker` | identificador textual do instrumento | `PETR4` |
| `quantity` | quantidade assinada e diferente de zero | `100` ou `-25` |
| `price` | preço positivo do instrumento | `38.42` |
| `asset_class` | classe de ativo suportada | `equity` |
| `currency` | código de moeda com três letras | `BRL` |

### Opcional

| Campo canônico | Descrição | Ausência |
|---|---|---|
| `sector` | classificação setorial textual | posição aceita com `MISSING_OPTIONAL_SECTOR` |

### Aliases de cabeçalho

Cabeçalhos ignoram caixa, espaços, acentos e separadores. Os aliases iniciais são:

| Campo | Aliases |
|---|---|
| `ticker` | `ticker`, `symbol`, `codigo`, `código`, `ativo` |
| `quantity` | `quantity`, `qty`, `quantidade` |
| `price` | `price`, `preco`, `preço`, `unit_price`, `preco_unitario` |
| `asset_class` | `asset_class`, `classe`, `classe_ativo`, `classe de ativo` |
| `currency` | `currency`, `ccy`, `moeda` |
| `sector` | `sector`, `setor` |

Duas colunas que normalizam para o mesmo nome ou mapeiam para o mesmo campo tornam o
cabeçalho ambíguo e geram erro estrutural.

Colunas declaradas sem mapeamento são preservadas em `raw_fields`, ignoradas pelo
domínio e informadas por `EXTRA_COLUMNS_IGNORED`. Valores adicionais que não possuem
coluna no cabeçalho geram `TOO_MANY_FIELDS` na linha.

## Classes de ativo

Os valores são normalizados da mesma forma que os cabeçalhos:

| Classe | Valores aceitos inicialmente |
|---|---|
| `equity` | `equity`, `equities`, `stock`, `stocks`, `acao`, `ações` |
| `fixed_income` | `fixed_income`, `renda fixa`, `bond`, `bonds` |
| `fx` | `fx`, `forex`, `cambio`, `cambial` |
| `cash` | `cash`, `caixa` |
| `commodity` | `commodity`, `commodities` |
| `fund` | `fund`, `funds`, `fundo`, `fundos` |
| `derivative` | `derivative`, `derivatives`, `derivativo`, `derivativos` |
| `other` | `other`, `outro` |

O importador não consulta uma API para reconhecer ticker ou classe.

## Números

Quantidade e preço são convertidos diretamente de texto para `Decimal`.

```text
Válido:   100, -25, 38.42, 0.005
Inválido: 1.000,50 ou 38,42
```

O ponto é o único separador decimal e não há separador de milhar. A regra é
independente do delimitador CSV. Isso mantém a conversão determinística; suporte a
locales poderá ser introduzido futuramente como configuração explícita.

Depois do parsing, aplicam-se as invariantes da Fase 2:

- quantidade finita e diferente de zero;
- preço finito e estritamente positivo;
- quantidade negativa representa posição vendida;
- `NaN` e infinito são rejeitados.

## Exemplo válido

```csv
ticker,quantity,price,asset_class,currency,sector
ZEUS_EQ1,100,25.40,equity,BRL,Energy
ZEUS_EQ2,50,70.00,equity,BRL,Materials
ZEUS_FUND1,-10,126.30,fund,BRL,Fund
```

Uma cópia sintética está disponível em
[`assets/samples/portfolio.csv`](../../assets/samples/portfolio.csv).

## Resultado estruturado

`ImportResult` registra:

- nome da fonte;
- encoding e delimitador efetivos;
- mapeamento de cada coluna;
- linhas revisáveis em ordem de origem;
- resumo de válidas, avisos, erros e posições aceitas;
- carteira parcial ou completa quando existe posição aceita;
- problemas globais do arquivo.

Cada `ImportRow` contém:

- número da linha física final do registro;
- status `valid`, `warning` ou `error`;
- campos originais preservados;
- posição construída quando aceita;
- problemas estruturados daquela linha.

Em campos CSV com múltiplas linhas, `line_number` representa a última linha física do
registro conforme o parser da biblioteca padrão.

### Status

- **valid:** posição construída sem problema;
- **warning:** posição construída, mas existe advertência não fatal;
- **error:** posição rejeitada; as demais linhas continuam sendo analisadas.

`ImportResult.is_partial` é verdadeiro quando coexistem posições aceitas e linhas com
erro. Uma carteira com erros não perde os problemas: a interface futura deverá
apresentá-los antes de executar análises.

## Erros estruturais

Erros que impedem interpretar o arquivo inteiro geram `PortfolioImportError`:

| Código | Situação |
|---|---|
| `FILE_NOT_FOUND` | caminho inexistente |
| `FILE_READ_ERROR` | arquivo inacessível ou caminho inadequado |
| `INVALID_FILE_ENCODING` | bytes não representam UTF-8 |
| `EMPTY_FILE` | nenhum conteúdo utilizável |
| `NO_DATA_ROWS` | cabeçalho sem posições |
| `MALFORMED_CSV` | aspas ou estrutura CSV inválida |
| `EMPTY_COLUMN_NAME` | cabeçalho contém coluna vazia |
| `DUPLICATE_SOURCE_COLUMN` | nomes de origem duplicados após normalização |
| `DUPLICATE_COLUMN_MAPPING` | dois aliases apontam para o mesmo campo |
| `MISSING_REQUIRED_COLUMNS` | campo canônico obrigatório ausente |

Esses erros não retornam linhas porque o contrato necessário para interpretá-las não é
confiável.

## Problemas de linha

Problemas recuperáveis permanecem em `ImportResult`:

| Código | Severidade típica |
|---|---|
| `MISSING_REQUIRED_VALUE` | error |
| `MISSING_OPTIONAL_SECTOR` | warning |
| `INVALID_DECIMAL` | error |
| `ZERO_QUANTITY` | error |
| `NON_FINITE_QUANTITY` | error |
| `NON_POSITIVE_PRICE` | error |
| `NON_FINITE_PRICE` | error |
| `INVALID_CURRENCY_CODE` | error |
| `UNSUPPORTED_ASSET_CLASS` | error |
| `DUPLICATE_POSITION` | error na ocorrência posterior |
| `TOO_MANY_FIELDS` | error |

## Exemplo de uso

```python
from pathlib import Path

from zeus_risk.importers import CsvPortfolioImporter

result = CsvPortfolioImporter().import_file(
    Path("assets/samples/portfolio.csv"),
    portfolio_name="Example Portfolio",
)

for row in result.rows:
    print(row.line_number, row.status, [issue.code for issue in row.issues])

if result.portfolio is not None:
    print(result.portfolio.valuations())
```

## Hipóteses e limitações

- todo o arquivo é lido em memória na Fase 3;
- não há detecção automática de encoding;
- não há separador decimal por locale;
- linhas completamente vazias são ignoradas;
- a primeira posição de uma chave ticker/moeda é aceita e ocorrências posteriores são
  erros;
- não há edição de célula, confirmação visual ou escolha interativa de mapeamento;
- não há consulta externa para validar existência do ticker;
- XLSX usa um adapter separado com o mesmo contrato; ainda não há conversão cambial ou
  dados históricos;
- dados originais podem conter informação sensível e não devem ser copiados para logs
  indiscriminadamente.

## Estratégia de testes

- aliases em português e inglês;
- vírgula, ponto e vírgula e delimitador explícito;
- UTF-8 com BOM e arquivo com bytes inválidos;
- erros estruturais de cabeçalho e quoting;
- múltiplos problemas independentes na mesma linha;
- continuidade após linha inválida;
- posição vendida e carteira multimoeda;
- duplicidades e colunas extras;
- fixture versionada e amostra sintética offline;
- ausência de rede, pandas ou PySide6.
