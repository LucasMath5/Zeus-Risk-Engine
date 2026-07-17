# Formato de projeto desktop

## Objetivo

Um arquivo `*.zeus.json` preserva o estado mínimo necessário para reabrir o fluxo
desktop: nome, referências aos arquivos de entrada, worksheet, método de retorno e
configuração do risco histórico. Ele não incorpora posições, preços ou resultados e
não substitui os arquivos originais.

## Schema 1.0

```json
{
  "schema_version": "1.0",
  "software_version": "0.1.0",
  "name": "Historical Risk Demo",
  "portfolio": {
    "path": "risk_portfolio.csv",
    "worksheet_name": null
  },
  "market_data": {
    "path": "market_prices.csv"
  },
  "risk": {
    "model": "historical",
    "return_method": "simple",
    "confidence_level": "0.5",
    "horizon_days": 1,
    "window": 2,
    "quantile_method": "nearest_rank"
  }
}
```

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | string | deve ser exatamente `1.0` |
| `software_version` | string | versão que gravou o arquivo; não substitui o schema |
| `name` | string | não vazio, até 120 caracteres |
| `portfolio.path` | string | referência relativa ou absoluta para CSV/XLSX |
| `portfolio.worksheet_name` | string ou `null` | obrigatória para selecionar worksheet quando aplicável |
| `market_data.path` | string | referência para o CSV longo de preços |
| `risk.model` | string | `historical` na Fase 10 |
| `risk.return_method` | string | `simple` ou `log` |
| `risk.confidence_level` | string decimal | estritamente entre zero e um |
| `risk.horizon_days` | inteiro | horizonte positivo e representável na interface |
| `risk.window` | inteiro | janela positiva e suficiente para resolver a cauda |
| `risk.quantile_method` | string | `nearest_rank` |

O nível de confiança é texto decimal para não herdar aproximações binárias do JSON.
Booleanos não são aceitos como inteiros. Campos ausentes, desconhecidos ou duplicados
são rejeitados para impedir que erros de digitação sejam ignorados.

## Resolução de caminhos

Ao salvar, uma referência localizada dentro da pasta do projeto é escrita com barras
portáveis e caminho relativo. Referências externas permanecem absolutas. Ao abrir,
caminhos relativos são resolvidos a partir da pasta do próprio `*.zeus.json`, nunca do
diretório de execução do programa.

Mover apenas o JSON não move os dados. Para um projeto portátil, mantenha o JSON, a
carteira e os preços na mesma árvore de diretórios, como em `assets/samples`.

## Validação e segurança

- limite de um megabyte antes do parsing;
- codificação UTF-8 obrigatória;
- parsing JSON estrito com detecção de chaves duplicadas;
- conjunto exato de campos em cada objeto;
- referências precisam existir e identificar arquivos regulares;
- configuração passa novamente pelas invariantes do domínio;
- gravação usa arquivo temporário, `fsync` e substituição atômica;
- nenhum conteúdo importado é interpretado como código.

Falhas usam códigos estáveis, incluindo:

| Código | Significado |
|---|---|
| `PROJECT_FILE_NOT_FOUND` | arquivo de projeto ausente |
| `INVALID_PROJECT_JSON` | sintaxe JSON inválida |
| `DUPLICATE_PROJECT_FIELD` | chave repetida em um objeto |
| `MISSING_PROJECT_FIELD` | campo obrigatório ausente |
| `UNKNOWN_PROJECT_FIELD` | campo não reconhecido |
| `UNSUPPORTED_PROJECT_SCHEMA_VERSION` | schema diferente de `1.0` |
| `PROJECT_PORTFOLIO_FILE_NOT_FOUND` | carteira referenciada ausente |
| `PROJECT_MARKET_DATA_FILE_NOT_FOUND` | preços referenciados ausentes |
| `PROJECT_CONFIGURATION_NOT_REPRESENTABLE` | configuração válida, mas fora dos controles atuais |

## Compatibilidade

A Fase 10 possui somente o schema `1.0`. Uma versão desconhecida gera erro explícito;
não existe migração ou coerção automática. Uma futura alteração incompatível exige
novo schema, testes de migração e atualização deste documento.

## Exemplo executável

Abra `assets/samples/historical-risk-demo.zeus.json` pelo menu **Arquivo → Abrir
projeto**. As referências relativas carregam os dois CSVs sintéticos da mesma pasta.
