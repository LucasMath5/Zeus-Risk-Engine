# Glossário

## Objetivo e convenções

Este glossário estabelece vocabulário comum para produto, domínio quantitativo e
arquitetura. Quando um termo tiver várias definições possíveis, a implementação
deve escolher uma delas explicitamente em configuração, documentação do modelo
ou ADR.

Termos de código serão preferencialmente escritos em inglês; a interface e a
documentação podem exibir a tradução em português. Siglas são mantidas quando
forem a forma mais reconhecida no mercado.

## Termos de domínio e risco

| Termo | Definição no projeto |
|---|---|
| **Ativo (`asset`)** | Bem ou fator financeiro ao qual uma posição está exposta. Não é necessariamente sinônimo do instrumento negociado. |
| **Backtesting** | Comparação sistemática de previsões de risco passadas com resultados realizados, incluindo identificação e análise de exceções. |
| **Carteira (`Portfolio`)** | Agregado identificado de posições, com nome e data de referência, sujeito a validações e análises. |
| **Cauda** | Região extrema de uma distribuição. Para risco de perda, é a região além do quantil associado ao VaR conforme a convenção de sinal. |
| **Classe de ativo (`asset_class`)** | Classificação controlada de uma posição, como ações, renda fixa, câmbio ou caixa. A taxonomia suportada será versionada. |
| **Concentração** | Grau em que exposição ou risco está distribuído em poucos ativos, setores, moedas ou outras dimensões. Na Fase 6, usa HHI sobre pesos brutos. |
| **Confiança (`confidence level`)** | Probabilidade associada ao quantil de risco, por exemplo 95% ou 99%. Não representa garantia de que a perda não será excedida. |
| **Correlação** | Medida adimensional de dependência linear entre duas séries, limitada a -1 e 1 quando bem definida. Não implica causalidade. |
| **Covariância** | Medida conjunta de variação linear cuja unidade depende das séries utilizadas. |
| **Data-base (`reference date`)** | Data à qual carteira, preços ou resultado se referem. Deve ser diferente da data em que a execução ocorreu quando aplicável. |
| **Drawdown** | Queda relativa não positiva da riqueza em relação ao pico anterior: `W_t / pico_t - 1`. |
| **EWMA** | *Exponentially Weighted Moving Average*; método que atribui peso exponencialmente decrescente a observações passadas. |
| **Exceção de VaR** | Observação em que a perda realizada excede o limite de VaR segundo a mesma convenção e horizonte. |
| **Expected Shortfall (ES/CVaR)** | Perda média condicional na cauda além do limiar de VaR, segundo definição amostral ou distribucional documentada. Considera a severidade além do quantil. |
| **Exposição bruta** | Soma dos valores absolutos das exposições, sem compensar posições compradas e vendidas. |
| **Exposição líquida** | Soma algébrica das exposições, respeitando o sinal de cada posição. |
| **Frequência** | Periodicidade das observações, como diária ou mensal. Frequência observada e regra de anualização não devem ser confundidas. |
| **Horizonte** | Período futuro sobre o qual o risco é expresso, por exemplo um ou dez dias. A forma de escalonamento deve ser explícita. |
| **Índice Herfindahl (HHI)** | Soma dos quadrados dos pesos brutos. Varia de mais de zero a 1; valores maiores indicam maior concentração. |
| **Instrumento (`Instrument`)** | Entidade negociável identificada por ticker e atributos como classe, moeda e setor. |
| **Janela (`window`)** | Quantidade ou intervalo de observações históricas usadas por um cálculo. |
| **Maximum drawdown** | Maior magnitude positiva de drawdown no período, acompanhada das datas de pico, vale e eventual recuperação. |
| **Moeda-base** | Moeda na qual os valores agregados da carteira são expressos. Conversão cambial não deve ser presumida. |
| **Monte Carlo** | Método de simulação que gera cenários aleatórios segundo um modelo e uma seed controlável para estimar a distribuição de resultados. |
| **P&L** | *Profit and Loss*; ganho ou perda em um período, cuja base de cálculo deve ser compatível com o risco previsto. |
| **Peso** | Participação de uma posição em uma base agregada. Na Fase 2, a base é explicitamente líquida ou bruta. |
| **Peso bruto** | Valor absoluto da posição dividido pela exposição bruta da mesma moeda; é não negativo e a soma é aproximadamente 1. |
| **Peso líquido** | Valor assinado da posição dividido pelo valor líquido da mesma moeda; pode ser negativo ou maior que 1 e não existe quando o denominador é zero. |
| **Posições efetivas** | Recíproco do HHI (`1 / HHI`), interpretado como quantidade equivalente de posições brutas igualmente ponderadas. |
| **Posição (`Position`)** | Quantidade de um instrumento mantida em uma carteira, acompanhada do preço e classificações necessárias. |
| **Preço ajustado** | Série alterada para refletir eventos como dividendos e desdobramentos. A origem e o tipo do ajuste devem ser metadados. |
| **Retorno logarítmico** | `ln(P_t / P_{t-1})`; é aditivo no tempo, mas não corresponde diretamente ao percentual simples para variações grandes. |
| **Retorno simples** | `(P_t / P_{t-1}) - 1`; representa a variação percentual entre duas observações. |
| **Stress testing** | Avaliação do impacto de choques severos, hipotéticos ou históricos, sem interpretar sua magnitude como probabilidade. |
| **Ticker** | Identificador textual do instrumento dentro de uma fonte ou mercado. Pode não ser universalmente único sem contexto adicional. |
| **VaR histórico** | Quantil de perdas estimado da distribuição empírica de retornos ou P&L históricos, segundo método de quantil documentado. |
| **VaR paramétrico** | Estimativa de VaR derivada de uma distribuição e parâmetros assumidos, inicialmente a distribuição normal. |
| **Value at Risk (VaR)** | Limiar de perda para um horizonte e confiança definidos. No produto, convenção de sinal, moeda, janela e método devem acompanhar todo resultado; a convenção concreta será formalizada antes da Fase 7. |
| **Valor de mercado** | Quantidade multiplicada pelo preço de referência, antes de conversões ou multiplicadores que deverão ser explícitos. |
| **Volatilidade** | Raiz da variância dos retornos. Na Fase 6, o estimador amostral é padrão e a anualização diária usa fator explícito, inicialmente 252. |

## Dados, validação e execução

| Termo | Definição no projeto |
|---|---|
| **Cache** | Cópia local identificável de dados obtidos anteriormente, usada para desempenho e reprodutibilidade; não substitui metadados de origem. |
| **Código de validação** | Identificador estável e legível por máquina para uma classe de problema, como `MISSING_REQUIRED_FIELD`. |
| **Configuração de risco (`RiskConfiguration`)** | Objeto validado e versionável que contém os parâmetros efetivos dos modelos. |
| **Erro (`error`)** | Problema que invalida um item ou impede uma operação dependente dele. |
| **Execução (`execution`)** | Ocorrência identificada de um caso de análise com versão, horário, entradas, configuração, resultados, duração e problemas. |
| **Hash de entrada** | Resumo criptográfico calculado sobre uma representação canônica das entradas para auxiliar integridade e reprodução; não contém os dados originais. |
| **ImportResult** | Resultado estruturado de importação que reúne proveniência, mapeamentos, linhas revisáveis, resumo, problemas e carteira aceita parcial ou integralmente. |
| **ImportRow** | Representação de uma linha importada com número físico, valores originais, status, problemas e posição opcional. |
| **ImportStatus** | Estado `valid`, `warning` ou `error` atribuído a uma linha após parsing e validação. |
| **Informação (`info`)** | Observação contextual que não indica degradação ou invalidade. |
| **Metadados de mercado (`MarketDataMetadata`)** | Provider, fonte, hash, frequência, instante de carga, intervalo, contagens e tratamento de ausências de um conjunto de séries. |
| **Missing value** | Observação ausente. Remoção, preenchimento ou alinhamento deve seguir uma política declarada e registrada. |
| **Conjunto de dados de mercado (`MarketDataSet`)** | Coleção validada de séries com chaves únicas e metadados reconciliados de frequência, período e contagens. |
| **Observação de preço (`PriceObservation`)** | Par imutável de data de calendário e preço `Decimal` finito e estritamente positivo. |
| **Política de alinhamento (`AlignmentPolicy`)** | Regra explícita de interseção ou união das datas de várias séries; união preserva ausências como `None` e nenhuma opção preenche preços. |
| **Política de valor ausente (`MissingValuePolicy`)** | Tratamento de preço ausente na entrada: erro por padrão ou descarte explícito com aviso. Não autoriza descartar preço inválido. |
| **Problema de validação (`ValidationIssue`)** | Objeto com severidade, código, mensagem e, quando aplicável, campo, item e localização. |
| **Reprodutibilidade** | Capacidade de obter o mesmo resultado com as mesmas entradas, configuração, versão e política numérica dentro de tolerância declarada. |
| **Resultado estruturado** | Objeto tipado que reúne valores, unidade, parâmetros, metadados e problemas, em vez de um dicionário sem contrato. |
| **Série de retornos (`ReturnSeries`)** | Retornos finitos de uma série ou carteira, ordenados por data e identificados por método e frequência. |
| **Tabela de retornos (`ReturnTable`)** | Retornos retangulares e completamente alinhados, com uma coluna por `PriceSeriesKey`. |
| **Série de preços (`PriceSeries`)** | Sequência diária não vazia de observações para uma `PriceSeriesKey`, com datas únicas e crescentes. |
| **Chave de série (`PriceSeriesKey`)** | Identidade normalizada `(ticker, currency)` de uma série de preços. |
| **Schema version** | Identificador da estrutura de um arquivo ou mensagem persistida, usado para validar compatibilidade e migração. |
| **Severidade** | Classificação `info`, `warning` ou `error` atribuída a um problema de validação. |
| **Aviso (`warning`)** | Problema não fatal que pode reduzir qualidade ou interpretação e deve acompanhar o resultado. |
| **Worksheet** | Planilha nomeada dentro de um workbook XLSX; uma importação processa exatamente uma worksheet e preserva seu nome. |

## Arquitetura e engenharia

| Termo | Definição no projeto |
|---|---|
| **Adapter** | Implementação que traduz entre um contrato interno e uma tecnologia externa, como CSV, XLSX, SQLite ou Qt. |
| **ADR** | *Architecture Decision Record*; registro versionado do contexto, decisão, alternativas e consequências de uma escolha arquitetural. |
| **Camada de aplicação** | Coordena casos de uso, transações e chamadas a contratos, sem conter fórmulas quantitativas ou detalhes de widgets. |
| **Core quantitativo** | Código de domínio e cálculo financeiro/estatístico executável sem interface gráfica. |
| **Domínio** | Modelos, invariantes, tipos de valor e regras que expressam o problema financeiro. |
| **DTO** | Objeto de transporte com contrato explícito usado em fronteiras; não substitui automaticamente uma entidade de domínio. |
| **Decimal** | Tipo numérico usado no domínio para quantidade, preço, valor e pesos, construído preferencialmente a partir de texto para evitar herdar aproximações binárias de `float`. |
| **Port** | Protocolo ou interface definido pelo lado consumidor para acessar uma capacidade externa sem depender de sua implementação. |
| **Provider de dados de mercado** | Port que fornece séries e metadados; implementações futuras podem usar arquivos, demonstrações, cache ou APIs. |
| **Repository** | Port orientado à persistência e recuperação de entidades ou agregados, introduzido apenas quando houver caso de uso real. |
| **Worker** | Componente que executa operação demorada fora do fluxo da interface e comunica progresso, cancelamento, resultado e falha. |

## Termos que exigirão decisão formal

Antes da implementação correspondente, devem ser definidos e documentados:

- convenção de sinal de perdas, VaR e Expected Shortfall;
- método de quantil empírico;
- calendários e fatores de anualização alternativos ao padrão diário 252;
- calendários, timezone de observações e alinhamentos além das políticas locais da
  Fase 5;
- política de missing values para cálculos que recebam a união de séries;
- moeda-base e eventual conversão;
- arredondamento de exibição e tolerâncias de modelos além da precisão analítica de 34
  dígitos fechada na Fase 6.
