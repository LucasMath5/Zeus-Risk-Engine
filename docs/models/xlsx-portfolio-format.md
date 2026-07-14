# Formato XLSX de carteira

## Objetivo

Este documento define o contrato de importação XLSX entregue na Fase 4. O adapter lê
uma worksheet local, converte suas células para o contrato tabular compartilhado e usa
as mesmas validações de domínio, aliases, status e resultados da importação CSV.

`Instrument`, `Position` e `Portfolio` permanecem independentes de workbooks,
planilhas, coordenadas de células e `openpyxl`.

## Dependências e segurança

O adapter utiliza:

- `openpyxl>=3.1.5,<4` para leitura de arquivos Office Open XML;
- `defusedxml>=0.7.1,<1` para endurecer o parsing XML usado pelo `openpyxl`;
- `types-openpyxl` e `types-defusedxml` somente durante o desenvolvimento.

A [documentação de segurança do openpyxl](https://openpyxl.readthedocs.io/en/stable/)
recomenda `defusedxml` para proteção contra ataques XML de expansão. O Zeus também
limita o tamanho comprimido e descomprimido do arquivo antes do parsing.

O workbook é aberto com:

- `read_only=True`, para consumir células em fluxo;
- `data_only=False`, para identificar e rejeitar fórmulas em vez de aceitar valores em
  cache;
- `keep_links=False`, para não preservar links externos;
- macros não são carregadas, pois somente a extensão `.xlsx` é aceita.

Nenhuma fórmula é executada ou recalculada.

## Formatos aceitos

| Extensão | Estado | Motivo |
|---|---|---|
| `.xlsx` | aceita | formato Office Open XML sem macros |
| `.xls` | rejeitada | formato binário legado fora do escopo |
| `.xlsm` | rejeitada | macros fora do escopo e da política de entrada |
| `.xltx` / `.xltm` | rejeitada | templates não são carteiras suportadas |

Um arquivo renomeado para `.xlsx` ainda precisa ser um ZIP e possuir uma estrutura de
workbook válida.

## Seleção de worksheet

`list_worksheets()` retorna os nomes na ordem original do workbook.

- quando existe exatamente uma worksheet, ela é selecionada automaticamente;
- quando existem duas ou mais, `worksheet_name` é obrigatório;
- a comparação do nome é exata e diferencia maiúsculas e minúsculas;
- nome ausente ou vazio gera erro estrutural;
- worksheets ocultas continuam listadas e exigem seleção explícita quando ambíguas.

O nome selecionado é preservado em `ImportResult.worksheet_name`.

Proteção de worksheet é aceita porque ela restringe edição, mas não criptografa os
dados. Workbooks realmente criptografados não são suportados.

## Layout tabular

A primeira linha não vazia é interpretada como cabeçalho. Linhas completamente vazias
antes ou depois dela são ignoradas, preservando o número físico das demais linhas.

As colunas obrigatórias, a coluna opcional `sector`, os aliases em português e inglês,
as classes de ativo e as regras numéricas são exatamente as documentadas no
[formato CSV](csv-portfolio-format.md).

Cabeçalhos devem ser células textuais. Cabeçalho numérico, fórmula ou célula vazia entre
colunas torna o contrato ambíguo e interrompe a importação.

Colunas desconhecidas são preservadas com `EXTRA_COLUMNS_IGNORED`. Uma célula com valor
além da última coluna declarada gera `TOO_MANY_FIELDS` na linha correspondente.

## Tipos de célula

| Tipo recebido | Comportamento |
|---|---|
| texto | preservado e validado pelo contrato tabular |
| inteiro | convertido para representação decimal textual |
| ponto flutuante | convertido com `str` e depois para `Decimal` |
| vazia | tratada como valor ausente |
| fórmula | rejeitada com `FORMULA_NOT_ALLOWED` |
| erro do Excel | rejeitado com `CELL_ERROR` |
| booleano | rejeitado com `UNSUPPORTED_CELL_TYPE` |
| data ou horário | rejeitado com `UNSUPPORTED_CELL_TYPE` |
| outro tipo interno | rejeitado com `UNSUPPORTED_CELL_TYPE` |

Datas e booleanos não são transformados silenciosamente em números. Se um campo deve
conter uma data no futuro, seu formato e semântica precisarão de um contrato próprio.

Para números financeiros, as invariantes continuam no domínio:

- quantidade finita e diferente de zero;
- preço finito e positivo;
- quantidade negativa representa posição vendida;
- moeda e classe de ativo seguem as taxonomias suportadas.

## Proveniência e resultado

O XLSX retorna o mesmo `ImportResult` usado pelo CSV, com estas particularidades:

- `source_name`: caminho recebido;
- `worksheet_name`: worksheet efetivamente importada;
- `encoding`: `None`, pois o XML interno é tratado pela biblioteca;
- `delimiter`: `None`, pois não existe delimitador;
- `ImportRow.line_number`: número físico da linha na worksheet;
- `ImportedField.value`: representação textual original ou segura da célula.

Uma célula inválida preserva seu valor em `raw_fields`, mas fornece uma string vazia ao
parser do domínio. Isso evita transformar uma fórmula, data ou booleano em posição
válida por acidente.

## Limites padrão

`XlsxImportOptions` aplica limites positivos e configuráveis:

| Limite | Padrão |
|---|---:|
| tamanho comprimido do arquivo | 25 MiB |
| tamanho total descomprimido do ZIP | 100 MiB |
| linhas físicas da worksheet | 25.000 |
| colunas da worksheet | 100 |

O arquivo também é limitado a 2.048 entradas internas. Os limites reduzem risco de
consumo excessivo no fluxo síncrono atual; não representam uma garantia absoluta contra
todo arquivo malicioso.

## Erros estruturais específicos

| Código | Situação |
|---|---|
| `INVALID_FILE_PATH` | caminho não é `str` nem `Path` |
| `FILE_NOT_FOUND` | caminho inexistente |
| `FILE_READ_ERROR` | arquivo não pode ser inspecionado ou lido |
| `UNSUPPORTED_FILE_TYPE` | extensão diferente de `.xlsx` |
| `XLSX_FILE_TOO_LARGE` | tamanho comprimido acima do limite |
| `XLSX_ARCHIVE_TOO_LARGE` | conteúdo descomprimido acima do limite |
| `XLSX_ARCHIVE_TOO_COMPLEX` | número excessivo de entradas no ZIP |
| `ENCRYPTED_XLSX_NOT_SUPPORTED` | entrada criptografada |
| `INVALID_XLSX` | ZIP ou estrutura OOXML inválida |
| `EMPTY_WORKBOOK` | workbook sem worksheet utilizável |
| `WORKSHEET_SELECTION_REQUIRED` | várias worksheets sem escolha |
| `INVALID_WORKSHEET_NAME` | nome vazio ou com tipo inadequado |
| `WORKSHEET_NOT_FOUND` | worksheet solicitada não existe |
| `WORKSHEET_TOO_LONG` | dimensão excede o limite de linhas |
| `WORKSHEET_TOO_WIDE` | dimensão excede o limite de colunas |
| `EMPTY_WORKSHEET` | worksheet sem cabeçalho |
| `FORMULA_IN_HEADER` | fórmula encontrada no cabeçalho |
| `INVALID_HEADER_CELL_TYPE` | cabeçalho não textual |

Os erros compartilhados de cabeçalho e domínio permanecem com os mesmos códigos do
CSV, como `MISSING_REQUIRED_COLUMNS`, `DUPLICATE_COLUMN_MAPPING` e `NO_DATA_ROWS`.

## Problemas recuperáveis de linha

| Código | Situação |
|---|---|
| `FORMULA_NOT_ALLOWED` | célula de dados contém fórmula |
| `CELL_ERROR` | célula contém erro do Excel |
| `UNSUPPORTED_CELL_TYPE` | booleano, data/hora ou tipo interno não suportado |

Esses problemas rejeitam somente a linha. Linhas independentes continuam sendo
processadas e podem formar uma carteira parcial.

## Exemplo de uso

```python
from pathlib import Path

from zeus_risk.importers import XlsxPortfolioImporter

path = Path("portfolio.xlsx")
importer = XlsxPortfolioImporter()

print(importer.list_worksheets(path))

result = importer.import_file(
    path,
    worksheet_name="Positions",
    portfolio_name="Example Portfolio",
)

for row in result.rows:
    print(row.line_number, row.status, [problem.code for problem in row.issues])
```

## Estratégia de testes

Os testes criam workbooks sintéticos em diretórios temporários. Isso mantém cada cenário
legível no código e evita versionar fixtures binárias opacas.

São cobertos:

- uma e várias worksheets;
- seleção automática, explícita, ausente e inválida;
- equivalência de posições importadas por CSV e XLSX;
- aliases, números como texto e números nativos;
- posição vendida, duplicidade e valor além do cabeçalho;
- fórmulas, datas, booleanos e erros do Excel;
- workbook vazio, corrompido, protegido e com extensão incompatível;
- limites de arquivo, arquivo descomprimido, linhas e colunas;
- continuidade após erro de célula.

## Limitações atuais

- somente uma worksheet é importada por chamada;
- não há seleção por índice ou comparação de nome sem diferenciar caixa;
- células mescladas não recebem tratamento de negócio especial;
- estilos, comentários, imagens e validações do Excel são ignorados;
- fórmulas são rejeitadas mesmo quando possuem valor calculado em cache;
- não há `.xls`, `.xlsm`, senha, mapeamento visual ou recálculo;
- o processamento ainda é síncrono e será envolvido por worker apenas na fase prevista;
- dados originais podem ser sensíveis e não devem ser copiados integralmente para logs.
