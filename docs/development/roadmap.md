# Roadmap de desenvolvimento

## Princípios do roadmap

- Uma fase entrega uma capacidade pequena, demonstrável e testável.
- A numeração representa dependência lógica, não prazo de calendário.
- Uma fase não começa apenas porque a anterior recebeu código; seus critérios de
  saída e documentação também precisam estar satisfeitos.
- Funcionalidade planejada não autoriza implementação antecipada.
- O roadmap pode mudar mediante justificativa, atualização de escopo e ADR quando
  a mudança for estrutural.
- Versões serão definidas por entregas reais; a versão inicial planejada do
  projeto é 0.1.0.

## Estado das fases

| Fase | Entrega principal | Dependências | Critério resumido de saída | Estado |
|---:|---|---|---|---|
| 0 | planejamento e especificação | nenhuma | visão, escopo, casos, glossário, arquitetura, roadmap e ADRs revisáveis | concluída |
| 1 | fundação do repositório | Fase 0 | pacote instalável, CLI mínima, metadados, qualidade e testes básicos | concluída |
| 2 | domínio de carteira | Fase 1 | instrumentos, posições, carteira, validações, valor e pesos testados | concluída |
| 3 | importação CSV | Fase 2 | normalização, parsing, problemas por linha e fixture de exemplo | concluída |
| 4 | importação XLSX | Fase 3 | seleção de planilha e mapeamento integrados à mesma validação | concluída |
| 5 | dados de mercado locais | Fases 2–3 | port, provider CSV, séries, metadados, alinhamento e cache testados | concluída |
| 6 | analytics básicos | Fases 2 e 5 | retornos, volatilidade, correlação, drawdown e concentração documentados | concluída |
| 7 | VaR histórico | Fase 6 | configuração, convenção, quantil, resultado e testes numéricos | concluída |
| 8 | Expected Shortfall | Fase 7 | cauda, comparação com VaR, documentação e testes | concluída |
| 9 | interface inicial | Fases 3 e 6–8 | importação, validação, posições e resultados em PySide6 | concluída |
| 10 | projetos e configurações | Fase 9 | salvar/carregar e JSON com schema validado | concluída |
| 11 | VaR paramétrico normal | Fase 6 | covariância, quantil normal e documentação reconciliados | planejada |
| 12 | EWMA | Fase 11 | lambda, recorrência, comparação e regressão numérica | planejada |
| 13 | backtesting | Fases 7, 11 e 12 | exceções, Kupiec, Christoffersen, traffic light e interpretação | planejada |
| 14 | processamento assíncrono | Fase 9 e fluxos pesados | progresso, cancelamento, falha e encerramento seguro | planejada |
| 15 | stress testing | Fases 2, 9 e 14 | cenários versionados, editor, impacto e contribuição | planejada |
| 16 | persistência SQLite | Fases 10 e 13–15 | repositories, migrações, projetos, execuções e histórico | planejada |
| 17 | relatórios | Fases 9–10 e 16 | exportações com parâmetros, metadados, avisos e testes | planejada |
| 18 | Monte Carlo | Fases 11, 14 e 17 | correlação, Cholesky, seed, convergência e performance | planejada |
| 19 | empacotamento | fluxo funcional estável | build, executável/instalador, assets, versão e smoke test | planejada |
| 20 | extensibilidade de modelos | pelo menos dois modelos estáveis | contrato extraído, registro interno e guia de extensão | planejada |

## Marcos do produto

### Marco A — Fundação verificável (Fases 0–2)

O repositório é instalável, possui documentação, regras de qualidade e um domínio
de carteira capaz de calcular valor de mercado e pesos sem interface.

### Marco B — Pipeline de dados local (Fases 3–5)

Uma carteira e seus preços entram por arquivos locais, geram problemas
estruturados e chegam ao núcleo como objetos validados e acompanhados de
metadados.

### Marco C — Primeiro motor de risco (Fases 6–8)

O núcleo calcula analytics, VaR histórico e Expected Shortfall com fórmulas,
convenções e casos de regressão numérica documentados.

### Marco D — Primeira versão funcional desktop (Fases 9–10)

O usuário percorre o fluxo mínimo na interface, consulta resultados e salva uma
configuração/projeto básico. O formato mínimo de exportação pode ser antecipado
para cumprir a definição da primeira versão funcional, sem antecipar todos os
formatos da Fase 17.

### Marco E — Validação e cenários (Fases 11–15)

Modelos adicionais podem ser comparados, submetidos a backtesting e stress, e
operações longas não bloqueiam a UI.

### Marco F — Auditoria e distribuição (Fases 16–19)

Execuções e resultados são persistidos, relatórios são reproduzíveis e a
aplicação pode ser distribuída em ambientes oficialmente testados.

### Marco G — Extensão controlada (Fase 20)

Uma interface de modelos é extraída de implementações reais e documentada sem
transformar o produto em uma plataforma de plugins externos prematuramente.

## Detalhamento da Fase 0

### Objetivo

Eliminar ambiguidades de propósito e arquitetura antes de iniciar o pacote.

### Entregas

- `docs/product-vision.md`;
- `docs/scope.md`;
- `docs/use-cases.md`;
- `docs/glossary.md`;
- `docs/architecture/overview.md`;
- `docs/development/roadmap.md`;
- ADR-001 sobre separação entre UI e core;
- ADR-002 sobre PySide6.

### Conceitos aprendidos

- diferença entre visão, escopo, requisito e caso de uso;
- atributos de qualidade e restrições arquiteturais;
- direção de dependências e ports and adapters;
- uso de ADRs para registrar decisões e consequências;
- definição de critérios de aceitação antes da implementação.

### Critérios de saída

- os documentos usam o mesmo nome, autor, pacote e objetivo;
- o que pertence à Fase 0 não é confundido com o MVP;
- itens fora do escopo e decisões pendentes estão explícitos;
- arquitetura impede dependência Qt no núcleo;
- proposta de estrutura não cria pastas vazias;
- links internos e referências a ADRs são válidos;
- pontos que exigem escolha do autor estão destacados.

### Revisão necessária

O autor ainda deve confirmar público prioritário, moeda-base, classe de ativo dos
exemplos, formato mínimo de exportação e sistemas operacionais pretendidos. O suporte
a posições vendidas foi decidido na Fase 2. As demais respostas refinam fases futuras.

## Fase 1 — Fundação concluída

### Objetivo

Foi criada uma fundação pequena e executável que comprova instalação, importação
do pacote, versionamento, CLI e ferramentas de qualidade, sem antecipar modelos
de domínio.

### Funcionalidades incluídas

- layout `src/zeus_risk` e versão 0.1.0;
- ponto de entrada CLI mínimo com nome e versão;
- `pyproject.toml` com metadados e grupos de desenvolvimento justificados;
- README inicial, licença MIT, changelog e guia de contribuição;
- pytest, Ruff e type checking configurados de maneira gradual;
- primeiro teste de instalação/importação e teste da CLI;
- workflow de CI mínimo após os comandos locais estarem estáveis.

### Arquivos entregues

```text
src/zeus_risk/__init__.py
src/zeus_risk/__main__.py
src/zeus_risk/_version.py
src/zeus_risk/cli.py
src/zeus_risk/py.typed
tests/unit/test_package.py
tests/unit/test_cli.py
tests/integration/test_module_entrypoint.py
pyproject.toml
README.md
LICENSE
CHANGELOG.md
CONTRIBUTING.md
.gitignore
.github/workflows/quality.yml
```

A decisão por PySide6 já está registrada, mas a biblioteca não foi declarada
porque ainda não existe integração gráfica. Dependências quantitativas também
permanecem ausentes até que uma fase realmente as utilize.

### Decisões fechadas na Fase 1

- Python mínimo 3.11, com testes de CI nos limites 3.11 e 3.14;
- `setuptools` como backend e metadados PEP 621 em `pyproject.toml`;
- Ruff como linter e formatter único, sem Black concorrente;
- mypy em modo estrito para `src` e testes;
- changelog no formato Keep a Changelog e intenção de Semantic Versioning;
- CLI `zeus-risk`, também executável por `python -m zeus_risk`.

### Evidências de conclusão

- instalação editável validada em ambiente virtual Python 3.12;
- `python -m zeus_risk --version` e `zeus-risk --version` retornam 0.1.0;
- Ruff, mypy estrito e sete testes passam localmente;
- cobertura reportada em 95%, sem meta artificial nesta fase;
- wheel e source distribution são construídos e o wheel passa por instalação de
  smoke test;
- workflow usa os mesmos comandos locais e aguarda validação remota após o push;
- README documenta instalação, execução, testes, arquitetura, roadmap, autor,
  licença e aviso de uso educacional;
- nenhum módulo financeiro vazio ou dependência de runtime foi criado.

### Testes previstos

- pacote expõe `__version__ == "0.1.0"`;
- CLI retorna código zero e mostra nome/versão;
- importação do core futuro não exige Qt — a regra começa simples e será ampliada;
- smoke test da instalação configurada.

### Commit sugerido para a Fase 1

```text
chore: establish Python package and quality tooling
```

## Fase 2 — Domínio de carteira concluído

### Objetivo

Foram modeladas as entidades mínimas de uma carteira e suas invariantes, permitindo
calcular valor de mercado e pesos sem depender de importadores, dados de mercado
ou interface gráfica.

### Funcionalidades incluídas

- enums ou objetos de valor mínimos para classe de ativo e moeda;
- `Instrument`, `Position` e `Portfolio` com type hints e invariantes;
- `ValidationSeverity` e `ValidationIssue` com códigos estáveis;
- cálculo de valor de mercado por posição e total da carteira;
- cálculo de pesos segundo uma base documentada;
- validações agregadas, como ticker duplicado e carteira vazia;
- testes unitários e casos numéricos manualmente verificáveis.

### Fora da Fase 2

- leitura de CSV ou XLSX;
- providers e séries de preços;
- retornos, volatilidade, drawdown, VaR ou Expected Shortfall;
- persistência e interface PySide6;
- taxonomias extensas sem uso no fluxo inicial.

### Arquivos entregues

```text
src/zeus_risk/domain/__init__.py
src/zeus_risk/domain/currency.py
src/zeus_risk/domain/enums.py
src/zeus_risk/domain/instrument.py
src/zeus_risk/domain/position.py
src/zeus_risk/domain/portfolio.py
src/zeus_risk/domain/validation.py
tests/unit/domain/test_instrument.py
tests/unit/domain/test_currency.py
tests/unit/domain/test_position.py
tests/unit/domain/test_portfolio.py
tests/unit/domain/test_validation.py
docs/models/portfolio-domain.md
docs/decisions/ADR-003-decimal-and-portfolio-weights.md
```

### Decisões fechadas na Fase 2

- `Decimal` representa quantidade, preço, valor de mercado e pesos;
- quantidade negativa representa posição vendida e quantidade zero é inválida;
- pesos possuem bases explícitas `net` e `gross`;
- carteira multimoeda é permitida, mas agregação sem moeda explícita é rejeitada;
- ticker é normalizado e a chave inicial de duplicidade é ticker mais moeda;
- invariantes impedem construção inválida e preservam `ValidationIssue` na exceção.

### Evidências de conclusão

- objetos inválidos não são construídos silenciosamente;
- valor líquido e bruto reconciliam com exemplos manuais;
- pesos líquidos e brutos reconciliam dentro de tolerância decimal explícita;
- problemas possuem severidade, código e localização estáveis;
- domínio importa sem PySide6 e sem bibliotecas de leitura de dados;
- Ruff, mypy e 63 testes são aprovados localmente, com 99% de cobertura;
- documentação e ADR explicam fórmulas, hipóteses, interpretação e limitações.

### Testes previstos

- instrumento válido e campos obrigatórios inválidos;
- posição comprada, vendida ou zero conforme a decisão adotada;
- cálculo manual de valor de mercado;
- carteira vazia, duplicidades e agregações;
- soma dos pesos dentro de tolerância explícita;
- imutabilidade ou proteção contra mutação indevida;
- ausência de `NaN` e infinito em entradas válidas.

### Commit sugerido para a Fase 2

```text
feat(portfolio): add core domain models and valuation
```

## Fase 3 — Importação CSV concluída

### Objetivo

Foi implementada a importação de carteira CSV para os modelos da Fase 2, preservando
valores de origem, número da linha e todos os problemas encontrados, sem interromper a
análise do arquivo no primeiro erro.

### Funcionalidades incluídas

- leitura CSV com a biblioteca padrão;
- normalização e aliases documentados de cabeçalho;
- validação de colunas obrigatórias;
- conversão explícita de quantidade e preço para `Decimal`;
- mapeamento de classe de ativo, moeda e setor;
- status `valid`, `warning` ou `error` por linha;
- `ImportResult` estruturado com posições aceitas, linhas e resumo;
- detecção de ticker/moeda duplicado no arquivo;
- arquivo sintético de exemplo e testes de integração.

### Fora da Fase 3

- XLSX, escolha de planilha ou mapeamento visual;
- correção de células dentro da aplicação;
- consulta externa para reconhecer tickers;
- dados de mercado, interface PySide6 ou persistência;
- pandas como dependência obrigatória para um fluxo que a biblioteca padrão atende.

### Arquivos entregues

```text
src/zeus_risk/importers/__init__.py
src/zeus_risk/importers/csv_portfolio.py
src/zeus_risk/importers/models.py
src/zeus_risk/exceptions/portfolio.py
tests/unit/importers/test_csv_portfolio.py
tests/unit/importers/test_models.py
tests/integration/test_csv_portfolio_import.py
tests/fixtures/portfolios/valid_portfolio.csv
assets/samples/portfolio.csv
docs/models/csv-portfolio-format.md
```

### Decisões fechadas na Fase 3

- UTF-8 e UTF-8 com BOM são aceitos, sem fallback silencioso de encoding;
- delimitador pode ser explícito ou detectado entre vírgula, ponto e vírgula, tab e
  barra vertical;
- aliases em português e inglês são normalizados sem acentos;
- coluna extra declarada é preservada com aviso, linha vazia é ignorada e setor ausente
  gera aviso não fatal;
- falha de arquivo/cabeçalho gera `PortfolioImportError`, enquanto falha recuperável
  permanece no `ImportRow`;
- valores originais são preservados no resultado, mas não devem ser copiados
  indiscriminadamente para logs;
- a primeira posição ticker/moeda é aceita e ocorrências posteriores são rejeitadas.

### Evidências de conclusão

- um erro de linha não impede o relatório das demais;
- posições válidas usam exatamente os modelos da Fase 2;
- cada problema identifica código, campo, item e linha;
- ausência de coluna obrigatória falha com erro de importação específico;
- nenhuma coerção silenciosa de números inválidos;
- exemplo funciona offline e não contém dados confidenciais;
- não foi adicionada dependência de runtime;
- Ruff e mypy aprovados, 94 testes aprovados e cobertura total de 98%;
- wheel e source distribution construídos, seguidos de smoke test do wheel.

### Testes previstos

- arquivo válido completo e setor opcional;
- cabeçalhos normalizados e aliases suportados;
- coluna obrigatória ausente, arquivo vazio e CSV malformado;
- quantidade/preço inválidos, `NaN`, infinito e quantidade zero;
- classe, moeda e ticker inválidos;
- duplicidades e múltiplos problemas no mesmo arquivo;
- codificação e delimitador segundo as políticas escolhidas.

### Commit sugerido para a Fase 3

```text
feat(import): add validated CSV portfolio importer
```

## Fase 4 — Importação XLSX concluída

### Objetivo

Foi implementada a importação de carteiras XLSX reutilizando os contratos de coluna,
linha, validação e resultado da Fase 3, com seleção explícita de worksheet e sem
executar fórmulas ou conteúdo da pasta de trabalho.

### Funcionalidades incluídas

- leitura de arquivos `.xlsx`;
- listagem e seleção de worksheet por nome;
- primeira planilha como padrão somente quando a escolha for inequívoca e documentada;
- reutilização de aliases, conversão decimal, domínio e status por linha;
- preservação do nome da planilha e da linha de origem;
- tratamento de células vazias, tipos numéricos e fórmulas;
- testes com workbooks sintéticos pequenos.

### Fora da Fase 4

- `.xls` legado e `.xlsm` com macros;
- edição ou recálculo de fórmulas;
- mapeamento visual de colunas;
- interface PySide6, drag-and-drop ou processamento assíncrono;
- planilhas de mercado ou relatórios como entrada de posições.

### Arquivos entregues

```text
src/zeus_risk/importers/tabular.py
src/zeus_risk/importers/xlsx_portfolio.py
tests/unit/importers/test_xlsx_portfolio.py
tests/integration/test_xlsx_portfolio_import.py
docs/models/xlsx-portfolio-format.md
pyproject.toml
```

### Decisões fechadas na Fase 4

- `openpyxl>=3.1.5,<4` lê OOXML e `defusedxml>=0.7.1,<1` endurece o parsing XML;
- uma única worksheet é automática; duas ou mais exigem nome explícito;
- fórmulas são carregadas como fórmulas e rejeitadas, mesmo que exista valor em cache;
- texto, inteiro e ponto flutuante são aceitos; datas, booleanos e erros são rejeitados;
- os limites padrão são 25 MiB comprimidos, 100 MiB descomprimidos, 25.000 linhas e
  100 colunas;
- aliases e validação de domínio foram extraídos para `tabular.py` e reutilizados sem
  acoplar `domain` ao formato;
- workbooks sintéticos são gerados nos testes, evitando fixtures binárias opacas.

### Evidências de conclusão

- CSV e XLSX produzem contratos equivalentes de revisão;
- seleção inválida de planilha gera erro específico;
- fórmulas e macros não são executadas;
- tipos de célula não sofrem coerção silenciosa;
- arquivos de teste são sintéticos, pequenos e criados em diretórios temporários;
- dependências novas estão documentadas e limitadas à leitura segura de XLSX;
- CSV e XLSX reconciliam posições, valores e resumo em teste de integração;
- Ruff e mypy aprovados, 117 testes aprovados e cobertura total de 97%;
- wheel e source distribution construídos, seguidos de instalação e smoke test XLSX.

### Testes entregues

- workbook válido com uma e várias planilhas;
- planilha selecionada por nome, ausente e vazia;
- cabeçalhos, aliases e campos opcionais compartilhados com CSV;
- números como texto e como célula numérica;
- fórmulas, datas, booleanos e erros de célula;
- arquivo corrompido, extensão incompatível e workbook protegido quando aplicável.

### Commit sugerido para a Fase 4

```text
feat(import): add XLSX portfolio importer
```

## Fase 5 — Dados de mercado locais concluída

### Objetivo

Foi modelado um pipeline offline de preços históricos que separa contratos de domínio,
leitura CSV, alinhamento e cache. A entrega preserva proveniência e problemas
estruturados sem antecipar cálculos quantitativos.

### Funcionalidades incluídas

- `PriceSeriesKey`, `PriceObservation`, `PriceSeries`, `MarketDataMetadata`,
  `MarketDataSet` e resultados imutáveis;
- frequência diária, preços `Decimal` positivos, datas únicas e crescentes;
- `MarketDataProvider` como `Protocol` orientado ao consumidor;
- provider CSV longo, UTF-8, local e protegido por limites de arquivo e linhas;
- aliases de cabeçalho em português e inglês e múltiplas séries por arquivo;
- problemas por linha com códigos estáveis e acumulação de erros independentes;
- política de preço ausente `error` ou `drop`, sempre registrada nos metadados;
- alinhamento determinístico por interseção ou união, sem preenchimento implícito;
- cache JSON schema 1, endereçado por SHA-256 e gravado atomicamente;
- exemplo e fixtures sintéticos, testes unitários e integração de ponta a ponta.

### Fora da Fase 5

- APIs externas, downloads ou credenciais;
- retorno, volatilidade, correlação ou drawdown, reservados à Fase 6;
- conversão cambial e escolha de moeda-base;
- banco de dados, UI ou processamento assíncrono;
- calendários de bolsa completos e preenchimento estatístico avançado.

### Arquivos entregues

```text
src/zeus_risk/domain/market_data.py
src/zeus_risk/market_data/__init__.py
src/zeus_risk/market_data/provider.py
src/zeus_risk/market_data/csv_provider.py
src/zeus_risk/market_data/alignment.py
src/zeus_risk/market_data/cache.py
tests/unit/domain/test_market_data.py
tests/unit/exceptions/test_market_data_error.py
tests/unit/market_data/
tests/integration/test_local_market_data_pipeline.py
tests/fixtures/market_data/
assets/samples/market_prices.csv
docs/models/market-data.md
```

### Decisões fechadas na Fase 5

- datas usam `datetime.date`, cargas usam `datetime` com timezone e a frequência inicial
  é somente diária;
- o CSV usa formato longo com `ticker,date,price,currency`, aliases controlados e ponto
  como separador decimal;
- `(ticker, currency)` identifica uma série e duplicar essa chave na mesma data é erro;
- preço deve ser `Decimal`, finito e estritamente positivo;
- preço ausente é erro por padrão; `drop` descarta apenas ausência e produz aviso;
- interseção mantém datas comuns; união mantém todas e usa `None`, sem preencher;
- SHA-256 dos bytes originais identifica conteúdo e chaveia o cache JSON schema 1;
- o cache preserva a fonte e reaplica todas as invariantes na leitura;
- os limites padrão síncronos são 25 MiB e 250.000 linhas.

### Evidências de conclusão

- domínio de mercado importa sem pandas, Qt ou provider concreto;
- provider local nunca acessa a rede;
- metadados identificam provider, fonte, hash, período, frequência, observações, séries e
  política de ausência;
- datas e preços inválidos produzem códigos estáveis;
- alinhamento é determinístico e preserva a política utilizada;
- cache não perde a referência à fonte nem altera silenciosamente os dados;
- testes reconciliam o CSV sintético, alinhamento e round trip do cache;
- Ruff e formatação aprovados, mypy estrito aprovado em 44 arquivos;
- 171 testes aprovados com cobertura total de 94%;
- 16 documentos Markdown válidos em UTF-8 e nenhum link interno quebrado;
- wheel e source distribution construídos, seguidos de instalação do wheel e smoke
  test de carga, alinhamento e cache.

### Testes entregues

- invariantes de chaves, observações, séries, metadados, conjunto e resultado;
- aliases, BOM, delimitadores, linhas fora de ordem e colunas extras;
- arquivo ausente, vazio, grande, malformado e com encoding inválido;
- datas, moedas, preços, campos e duplicidades inválidos;
- políticas `error` e `drop` para preço ausente;
- interseção, união, ausência de datas comuns e entradas incompatíveis;
- round trip do cache e rejeição de chave, encoding, JSON, schema e conteúdo inválidos;
- pipeline local completo sobre fixture e exemplo versionado.

### Commit sugerido para a Fase 5

```text
feat(market-data): add local price series provider
```

## Fase 6 — Analytics básicos concluída

### Objetivo

Foi entregue o primeiro núcleo quantitativo puro sobre séries validadas e alinhadas,
com fórmulas, convenções, resultados imutáveis e casos de regressão numérica
documentados.

### Funcionalidades incluídas

- retornos simples e logarítmicos por série;
- retorno de carteira com convenção explícita de pesos e rebalanceamento;
- média, variância, volatilidade, covariância e correlação;
- anualização diária com fator efetivo registrado;
- trajetória acumulada, drawdown e maximum drawdown;
- concentração por peso, incluindo índice Herfindahl quando aplicável;
- objetos imutáveis de configuração e resultado;
- erros quantitativos específicos para amostra insuficiente ou resultado indefinido;
- documentação matemática e testes manualmente reconciliáveis.

### Fora da Fase 6

- VaR e Expected Shortfall, reservados às Fases 7 e 8;
- estimação paramétrica normal, EWMA, Monte Carlo e backtesting;
- otimização de carteira, atribuição completa ou contribuição de risco;
- conversão cambial e aquisição de novos dados;
- interface PySide6, persistência ou relatórios.

### Decisões fechadas na Fase 6

- `Decimal` com contexto local de 34 dígitos e `ROUND_HALF_EVEN`, sem mutar o contexto
  global;
- retorno simples e logarítmico são opções explícitas, sem conversão silenciosa;
- agregação de retornos log de carteira passa pelo retorno simples ponderado antes de
  aplicar `ln`;
- variância amostral com `n - 1` é padrão e a populacional com `n` é suportada;
- anualização diária usa fator explícito, padrão 252, e não representa calendário;
- retorno de carteira usa pesos líquidos assinados e constantes da fotografia,
  equivalente a rebalanceamento por período;
- `None` alinhado é rejeitado; nenhuma observação é preenchida ou removida no core;
- drawdown é não positivo e maximum drawdown é magnitude positiva;
- HHI usa pesos brutos e posições efetivas são calculadas por `1 / HHI`;
- correlação com variância zero gera falha estruturada, nunca `NaN`.

### Arquivos entregues

```text
src/zeus_risk/core/analytics/__init__.py
src/zeus_risk/core/analytics/_decimal.py
src/zeus_risk/core/analytics/returns.py
src/zeus_risk/core/analytics/statistics.py
src/zeus_risk/core/analytics/drawdown.py
src/zeus_risk/core/analytics/concentration.py
src/zeus_risk/domain/analytics.py
src/zeus_risk/exceptions/analytics.py
tests/unit/core/analytics/
tests/integration/test_basic_analytics_pipeline.py
tests/regression/test_basic_analytics_reference.py
docs/concepts/basic-analytics.md
```

### Evidências de conclusão

- fórmulas e convenções são documentadas antes ou junto do código;
- funções quantitativas não importam arquivo, cache, Qt ou provider;
- entradas inválidas nunca retornam `NaN` ou infinito como sucesso;
- resultados informam método, frequência, amostra e anualização efetivos;
- exemplos pequenos reconciliam manualmente retornos, volatilidade e drawdown;
- covariância e correlação respeitam simetria e casos indefinidos explícitos;
- pipeline de integração percorre provider CSV, alinhamento, retornos, carteira,
  estatísticas, matrizes, drawdown e concentração;
- regressão preserva preços e resultados manualmente reconciliáveis;
- Ruff e formatação aprovados; mypy estrito aprovado em 61 arquivos;
- 209 testes aprovados com cobertura total de 91%;
- 17 documentos Markdown válidos em UTF-8 e nenhum link interno quebrado;
- wheel e source distribution construídos, seguidos de instalação do wheel e smoke
  test do pipeline quantitativo.

### Testes entregues

- retornos simples, logarítmicos e identidade temporal do log;
- tabelas completas, preços ausentes, séries incompatíveis e moedas diferentes;
- carteiras long-only, long/short, neutras e crescimento alavancado não positivo;
- agregação log de carteira pela fórmula correta;
- média, variância amostral/populacional, volatilidade e anualização;
- covariância/correlação simétricas, relação positiva/negativa e série constante;
- riqueza acumulada, pico, vale, recuperação e equivalência simples/log;
- HHI para pesos iguais, posições vendidas e carteiras multimoeda;
- contratos imutáveis, códigos de erro e regressão numérica manual.

### Commit sugerido para a Fase 6

```text
feat(analytics): add portfolio descriptive analytics
```

## Fase 7 — VaR histórico concluída

### Objetivo

Foi entregue Value at Risk histórico sobre séries diárias de retorno validadas, com
configuração imutável, convenção positiva de perda, nearest-rank documentado e
resultados reconciliáveis.

### Funcionalidades incluídas

- `HistoricalVaRConfiguration` com confiança, horizonte, janela e método de quantil;
- transformação explícita de retorno em perda por `perda = -retorno`;
- cenários móveis sobrepostos com composição simples ou soma logarítmica;
- seleção determinística dos cenários mais recentes;
- VaR relativo não negativo com quantil bruto preservado;
- resultado estruturado com configuração, unidade, convenção, rank, amostra e datas;
- validação exata de resolução mínima da cauda;
- falhas específicas para confiança, janela, amostra, quantil e escala inválidos;
- documentação matemática, exemplo manual e regressão numérica.

### Fora da Fase 7

- Expected Shortfall, reservado à Fase 8;
- VaR paramétrico normal, EWMA e Monte Carlo;
- backtesting, exceções e testes de cobertura;
- conversão cambial e agregação de carteiras multimoeda;
- interface PySide6, persistência, processamento assíncrono ou relatórios.

### Decisões fechadas na Fase 7

- nearest-rank usa `ceil(confiança × janela)`, base 1 e nenhuma interpolação;
- perda é o oposto do retorno e o VaR apresentado é `max(quantile_loss, 0)`;
- o método simples ou logarítmico da série é preservado sem conversão;
- horizonte usa retornos históricos móveis agregados, nunca raiz do tempo;
- janela mínima é `ceil(1 / (1 - confiança))`;
- a janela seleciona cenários depois da agregação de horizonte;
- a Fase 7 entrega somente unidade relativa; VaR monetário não presume base ou câmbio;
- resultado preserva amostra, rank, quantil, configuração, datas, unidade e convenção;
- as escolhas e alternativas estão formalizadas no ADR-004.

### Arquivos entregues

```text
src/zeus_risk/core/risk/__init__.py
src/zeus_risk/core/risk/historical_var.py
src/zeus_risk/domain/risk.py
src/zeus_risk/exceptions/risk.py
tests/unit/core/risk/test_historical_var.py
tests/unit/domain/test_risk.py
tests/unit/exceptions/test_risk_error.py
tests/integration/test_historical_var_pipeline.py
tests/regression/test_historical_var_reference.py
docs/concepts/historical-var.md
docs/decisions/ADR-004-historical-var-conventions.md
```

### Evidências de conclusão

- fórmula, sinal de perda e quantil estão documentados antes ou junto do código;
- a mesma amostra e configuração produzem resultado determinístico;
- confiança, horizonte, janela, método, amostra e datas acompanham o resultado;
- amostra insuficiente não retorna zero, `NaN` ou um quantil inventado;
- casos pequenos reconciliam ordenação das perdas e quantil manualmente;
- o cálculo não importa arquivo, provider, cache, Qt ou Expected Shortfall;
- testes unitários cobrem configuração, contratos, janela, horizonte simples/log,
  quantil, piso em zero e falhas estruturadas;
- integração percorre CSV local, alinhamento, retornos da carteira e VaR;
- regressão preserva um caso de 90% com dez perdas reconciliadas manualmente.
- Ruff e formatação aprovados; mypy estrito aprovado em 70 arquivos;
- 230 testes aprovados com cobertura total de 91%;
- 19 documentos Markdown válidos em UTF-8 e nenhum link interno quebrado;
- wheel e source distribution construídos, seguidos de instalação isolada do wheel e
  smoke test do VaR histórico.

### Commit sugerido para a Fase 7

```text
feat(risk): add historical value at risk
```

## Fase 8 — Expected Shortfall histórico concluída

### Objetivo

Foi entregue Expected Shortfall histórico sobre a mesma configuração, amostra e
convenção de perda do VaR histórico, com fronteira de cauda por rank, desempate
cronológico e reconciliação `ES >= VaR`.

### Funcionalidades incluídas

- cálculo da cauda empírica pelos ranks posteriores ao nearest-rank da Fase 7;
- desempate cronológico estável sem expandir a cauda;
- `HistoricalExpectedShortfallResult` imutável contendo o VaR efetivo;
- média bruta da cauda e ES não negativo em unidade relativa;
- amostra de cauda, contagem, datas, configuração e convenção preservadas;
- falhas específicas para cauda vazia, incompatível ou insuficiente;
- exemplo manual, integração e regressão numérica.

### Fora da Fase 8

- VaR paramétrico normal, EWMA e Monte Carlo;
- backtesting, exceções e testes de cobertura;
- VaR ou Expected Shortfall monetário e conversão cambial;
- interface PySide6, persistência, processamento assíncrono ou relatórios.

### Decisões fechadas na Fase 8

- a cauda contém exatamente os ranks `k+1 ... n`, excluindo o rank do VaR;
- empates usam valor, data final e data inicial como ordenação determinística;
- a média usa pesos iguais sobre os `n - k` ranks efetivos;
- `tail_mean_loss` preserva a média bruta e ES aplica `max(média, 0)`;
- o resultado de ES incorpora o `HistoricalVaRResult` em vez de duplicar configuração;
- a mesma precisão decimal local de 34 dígitos é usada na média;
- as escolhas e alternativas estão formalizadas no ADR-005.

### Arquivos entregues

```text
src/zeus_risk/core/risk/historical_expected_shortfall.py
src/zeus_risk/core/risk/__init__.py
src/zeus_risk/domain/risk.py
tests/unit/core/risk/test_historical_expected_shortfall.py
tests/unit/domain/test_risk.py
tests/integration/test_historical_expected_shortfall_pipeline.py
tests/regression/test_historical_expected_shortfall_reference.py
docs/concepts/historical-expected-shortfall.md
docs/decisions/ADR-005-historical-expected-shortfall-conventions.md
```

### Evidências de conclusão

- ES e VaR usam exatamente configuração, janela, horizonte, método e sinal compatíveis;
- a definição da cauda e o tratamento de empates são documentados;
- exemplos pequenos reconciliam seleção da cauda e média manualmente;
- para entradas válidas, ES é finito, não negativo e não inferior ao VaR;
- cauda insuficiente não retorna zero ou `NaN` como substituto de sucesso;
- o core continua independente de arquivo, provider, cache e Qt;
- testes unitários cobrem uma ou várias perdas na cauda, empates, ganhos e contratos;
- integração percorre CSV local, alinhamento, retornos da carteira, VaR e ES;
- regressão preserva VaR de 8% e ES de 12% no caso manual de 90%.
- Ruff e formatação aprovados; mypy estrito aprovado em 74 arquivos;
- 240 testes aprovados com cobertura total de 91%;
- 21 documentos Markdown válidos em UTF-8 e nenhum link interno quebrado;
- wheel e source distribution construídos, seguidos de instalação isolada do wheel e
  smoke test reconciliando VaR de 4% e ES de 10%.

### Commit sugerido para a Fase 8

```text
feat(risk): add historical expected shortfall
```

## Fase 9 — Interface inicial concluída

### Objetivo

Implementar a primeira interface desktop PySide6 funcional para importar e validar uma
carteira, visualizar posições, configurar o risco histórico e apresentar VaR e
Expected Shortfall sem mover regras quantitativas para a camada visual.

### Funcionalidades incluídas

- bootstrap da aplicação PySide6 e janela principal;
- fluxo para selecionar CSV ou XLSX e worksheet quando aplicável;
- painel de problemas estruturados de importação e validação;
- tabela somente leitura das posições aceitas;
- configuração de confiança, horizonte e janela;
- seleção de arquivo local de preços e execução do pipeline histórico;
- cartões ou tabela de VaR e Expected Shortfall com unidade e parâmetros;
- estados inicial, vazio, sucesso e falha compreensíveis;
- testes de models/controllers e smoke test GUI em modo offscreen.

### Fora da Fase 9

- salvar ou carregar projetos e configurações, reservados à Fase 10;
- VaR paramétrico, EWMA, backtesting e stress testing;
- workers e cancelamento de tarefas longas, reservados à Fase 14;
- persistência SQLite, histórico e relatórios;
- identidade visual final ou dashboards avançados.

### Decisões fechadas na Fase 9

- PySide6 `>=6.11.1,<6.12`, compatível com a faixa Python testada pelo projeto;
- `PortfolioRiskWorkflow` síncrono e independente de Qt como fronteira da aplicação;
- janela única com abas sequenciais para carteira e risco;
- `QAbstractTableModel` somente leitura para posições e problemas;
- execução síncrona limitada aos arquivos locais pequenos da fase, com botão bloqueado;
- estados vazio, pronto, executando, sucesso e falha, testados em modo offscreen;
- detalhes e alternativas formalizados no ADR-006.

### Arquivos entregues

```text
src/zeus_risk/app/__init__.py
src/zeus_risk/app/application.py
src/zeus_risk/app/main_window.py
src/zeus_risk/app/models.py
src/zeus_risk/app/views/
src/zeus_risk/application/
src/zeus_risk/application/portfolio_risk.py
tests/unit/application/test_portfolio_risk.py
tests/gui/conftest.py
tests/gui/test_qt_models.py
tests/gui/test_main_window.py
assets/samples/risk_portfolio.csv
docs/tutorials/first-desktop-workflow.md
docs/decisions/ADR-006-initial-desktop-composition.md
```

### Evidências de conclusão

- a aplicação abre e encerra com segurança no smoke test Qt offscreen;
- o usuário importa CSV/XLSX e visualiza problemas e posições sem terminal;
- o pipeline local de exemplo produz VaR e ES visíveis com configuração e unidade;
- a UI não recalcula retornos, VaR ou ES;
- falhas estruturadas são traduzidas em mensagens compreensíveis sem perder códigos;
- testes GUI executam em modo offscreen e não exigem rede ou diálogos reais;
- o tutorial reconcilia o exemplo de duas posições e dois cenários;
- 250 testes passam no Python 3.12 local com 90% de cobertura total;
- Ruff e formatação aprovados em 89 arquivos; mypy estrito aprovado;
- wheel e source distribution são construídos, o wheel reinstalado passa pela CLI e
  pelo smoke test Qt, e a inspeção nativa confirma contraste e layout.

### Commit sugerido para a Fase 9

```text
feat(ui): add initial portfolio risk workflow
```

## Fase 10 — Projetos e configurações concluída

### Objetivo

Salvar e reabrir o estado mínimo do fluxo desktop em um projeto JSON local, com schema
versionado, validação explícita e referências portáveis quando possível.

### Funcionalidades incluídas

- contrato imutável de projeto e configuração histórica;
- serialização JSON com `schema_version` e validação de campos desconhecidos;
- salvar como, abrir e indicação de alterações não salvas na janela;
- referências à carteira e aos preços sem incorporar dados confidenciais por padrão;
- migração explícita ou erro compreensível para schema incompatível;
- testes unitários, integração de round trip e estados GUI offscreen.

### Decisões fechadas na Fase 10

- extensão recomendada `*.zeus.json` e schema inicial `1.0`;
- `DesktopProject` imutável no domínio, sem dependência de Qt ou JSON;
- `ProjectWorkflow` como caso de uso e `JsonProjectStore` como adapter;
- arquivo referencial, sem copiar posições, preços ou resultados;
- caminhos relativos somente para referências dentro da pasta do projeto;
- confiança serializada como string decimal e inteiros JSON estritos;
- campos exatos, chaves duplicadas rejeitadas e limite de um megabyte;
- arquivo temporário sincronizado e substituição atômica no salvamento;
- abertura valida todas as fronteiras antes de substituir o estado atual;
- alternativas e consequências formalizadas no ADR-007.

### Fora da Fase 10

- banco SQLite, histórico de execuções e autenticação;
- autosave opaco ou armazenamento de carteiras sem consentimento;
- VaR paramétrico, EWMA, workers, relatórios e empacotamento final.

### Arquivos entregues

```text
src/zeus_risk/domain/project.py
src/zeus_risk/exceptions/project.py
src/zeus_risk/projects/json_store.py
src/zeus_risk/application/project_workflow.py
src/zeus_risk/app/main_window.py
src/zeus_risk/app/views/risk_page.py
tests/unit/domain/test_project.py
tests/unit/exceptions/test_project_error.py
tests/unit/projects/test_json_store.py
tests/unit/application/test_project_workflow.py
tests/integration/test_project_round_trip.py
tests/gui/test_main_window.py
assets/samples/historical-risk-demo.zeus.json
docs/models/project-file.md
docs/tutorials/save-and-reopen-project.md
docs/decisions/ADR-007-versioned-project-json.md
```

### Evidências de conclusão

- round trip preserva nome, referências, worksheet, retorno e configuração;
- o exemplo versionado abre e reproduz o pipeline histórico sem rede;
- campos ausentes, desconhecidos, duplicados ou incompatíveis falham por código;
- referências ausentes e configurações fora dos controles não são mascaradas;
- salvar/abrir, `Ctrl+S`, salvar como e indicador `*` funcionam na interface;
- abrir projeto inválido mantém o estado anterior;
- 273 testes passam no Python 3.14 local com 90% de cobertura total;
- Ruff e formatação aprovados em 99 arquivos; mypy estrito aprovado;
- wheel e source distribution são construídos; o wheel inclui os módulos e o sdist
  inclui também o projeto JSON de demonstração;
- o wheel reinstalado abre o projeto de demonstração e reproduz VaR `0,0000%` e ES
  `0,0328%` no smoke test Qt offscreen;
- inspeção visual nativa confirma o rótulo da Fase 10 e o fluxo restaurado.

### Commit sugerido para a Fase 10

```text
feat(projects): add versioned desktop project files
```

## Próxima etapa recomendada — Fase 11

### Objetivo

Implementar VaR paramétrico normal relativo como segundo modelo real, reutilizando
retornos e covariância existentes, com hipóteses, quantil, sinal, horizonte e
reconciliação matematicamente documentados.

### Funcionalidades inicialmente previstas

- configuração e resultado imutáveis do VaR paramétrico;
- média e volatilidade da carteira sob convenção explícita;
- quantil normal sem introduzir dependência desnecessária de framework tabular;
- escolha documentada entre VaR com média zero ou média estimada;
- regra de horizonte e unidade relativa;
- falhas estruturadas para variância, confiança ou amostra inválida;
- exemplo manual, regressão numérica e comparação conceitual com VaR histórico;
- integração ao workflow e à interface somente após o contrato do modelo estar validado.

### Fora da Fase 11

- EWMA, distribuições não normais, Monte Carlo e backtesting;
- VaR monetário, conversão cambial e decomposição de risco;
- seleção genérica prematura de plugins de modelos.

### Commit sugerido para a Fase 11

```text
feat(risk): add parametric normal var
```

## Template obrigatório para cada fase

Antes de implementar:

1. objetivo;
2. funcionalidades incluídas e excluídas;
3. conceitos envolvidos;
4. decisões e alternativas;
5. arquivos a criar ou alterar e motivo;
6. critérios de aceitação;
7. testes necessários;
8. sugestão de commit.

Depois de implementar:

1. resumo do resultado;
2. arquivos e responsabilidades;
3. explicação técnica e, quando aplicável, matemática;
4. comandos de instalação, execução e testes;
5. evidências de validação;
6. limitações e riscos restantes;
7. documentação atualizada;
8. próxima fase recomendada;
9. sugestão de commit Conventional Commits.

## Estratégia de versões e releases

- `0.x.y` indica evolução pré-1.0 e permite mudanças incompatíveis documentadas.
- incremento patch corrige comportamento sem ampliar contratos principais.
- incremento minor entrega capacidade utilizável e atualiza o changelog.
- `1.0.0` só será considerada quando o fluxo suportado, schemas públicos,
  empacotamento, documentação e política de compatibilidade estiverem definidos.
- uma fase não precisa corresponder exatamente a uma versão; releases agrupam
  resultados demonstráveis, não apenas estrutura interna.

## Critérios globais de qualidade

Toda fase aplicável deve:

- adicionar ou atualizar testes antes de ser considerada concluída;
- manter comandos locais e CI coerentes;
- preservar testes de regressão em vez de removê-los para acomodar mudanças;
- atualizar documentação e changelog quando alterar comportamento;
- registrar dependências novas e sua justificativa;
- evitar chamadas externas em testes unitários;
- manter exemplos básicos executáveis offline;
- declarar limitações conhecidas e decisões que dependem do autor.
