# Casos de uso

## Objetivo

Os casos de uso descrevem o comportamento observável desejado sem prescrever a
implementação. Eles orientam a definição dos casos de uso da camada de aplicação,
os testes de integração e, posteriormente, os fluxos da interface.

## Atores

- **Usuário:** estudante, analista ou desenvolvedor que prepara e executa a
  análise.
- **Sistema de arquivos local:** fornece carteiras, preços e configurações e
  recebe exportações.
- **Provedor de dados de mercado:** contrato interno que entrega séries e
  metadados; na primeira versão, usa arquivos locais.
- **Relógio e identificador de execução:** serviços internos usados futuramente
  para registrar data, duração e identidade de uma execução de forma testável.

## Convenções

- **MVP** identifica o fluxo da primeira versão funcional, não a Fase 0.
- **Posterior** identifica uma capacidade planejada, ainda fora do primeiro
  fluxo.
- Erros impedem o passo que depende do dado inválido; avisos permitem continuar
  mediante visibilidade e ficam associados ao resultado.
- Todo caso que produz cálculo deve retornar dados e problemas estruturados, sem
  depender de widgets.

## Mapa dos casos de uso

| ID | Caso de uso | Entrega | Prioridade |
|---|---|---|---:|
| UC-01 | Iniciar a aplicação | MVP | alta |
| UC-02 | Importar carteira CSV ou XLSX | MVP | alta |
| UC-03 | Revisar e validar posições | MVP | alta |
| UC-04 | Carregar preços locais | MVP | alta |
| UC-05 | Configurar uma análise | MVP | alta |
| UC-06 | Executar analytics básicos | MVP | alta |
| UC-07 | Executar risco histórico | MVP | alta |
| UC-08 | Interpretar e comparar resultados | MVP | alta |
| UC-09 | Exportar resultados básicos | MVP | média |
| UC-10 | Salvar e reabrir projeto | posterior | média |
| UC-11 | Consultar histórico de execuções | posterior | média |
| UC-12 | Cancelar uma tarefa longa | posterior | média |
| UC-13 | Executar backtesting | posterior | média |
| UC-14 | Executar cenário de stress | posterior | média |

## UC-01 — Iniciar a aplicação

**Objetivo:** acessar um ponto de entrada estável e compreender o próximo passo.

**Pré-condições:** instalação válida e ambiente suportado.

**Fluxo principal:**

1. O usuário inicia o Zeus Risk Engine.
2. O sistema carrega apenas configurações locais necessárias.
3. A tela inicial informa a versão e oferece iniciar ou abrir um fluxo suportado.
4. Se ainda não houver carteira, o sistema apresenta um estado vazio orientativo.

**Alternativas e falhas:** uma falha de inicialização apresenta mensagem
compreensível e preserva detalhes para diagnóstico; não é ocultada.

**Critérios de aceitação:** iniciar não exige internet; a interface não executa
cálculos no carregamento; versão e autoria são identificáveis.

## UC-02 — Importar carteira CSV ou XLSX

**Objetivo:** transformar um arquivo local em linhas normalizadas e problemas de
importação revisáveis.

**Pré-condições:** arquivo selecionado e acessível.

**Fluxo principal:**

1. O usuário seleciona um arquivo CSV ou XLSX.
2. O sistema aplica a política documentada de codificação ou seleção de worksheet.
3. Nomes de colunas conhecidos são normalizados.
4. Tipos são convertidos sem descartar silenciosamente a entrada original.
5. Cada linha recebe estado válido, aviso ou erro.
6. O sistema retorna posições candidatas, problemas e resumo da importação.

**Alternativas e falhas:** arquivo ausente, ilegível, vazio, worksheet ambígua,
cabeçalho inválido, campo obrigatório ausente, fórmula, tipo inválido e linha duplicada
produzem códigos de problema específicos. Erros de uma linha não encerram a revisão das
demais.

**Critérios de aceitação:** não há chamadas externas; a ordem das linhas pode ser
rastreada; nenhuma linha inválida se torna posição válida por coerção silenciosa.

## UC-03 — Revisar e validar posições

**Objetivo:** decidir se a carteira está apta para análise e entender como corrigir
problemas.

**Pré-condições:** resultado de importação disponível.

**Fluxo principal:**

1. O sistema mostra valores normalizados e estado de cada linha.
2. O usuário filtra ou seleciona erros e avisos.
3. Cada problema informa severidade, código, mensagem, campo e item afetado.
4. O sistema resume quantas linhas são válidas, possuem aviso ou erro.
5. A análise é habilitada somente quando seus pré-requisitos são satisfeitos.

**Alternativas e falhas:** avisos permitem prosseguir e são propagados; erros que
invalidam a carteira impedem cálculos dependentes, sem fechar a aplicação.

**Critérios de aceitação:** códigos são estáveis e testáveis; o mesmo conjunto de
entradas produz os mesmos problemas; cor não é o único indicador de severidade.

## UC-04 — Carregar preços locais

**Objetivo:** associar aos ativos séries históricas e metadados suficientes para
reprodução.

**Pré-condições:** carteira válida e fonte local configurada.

**Fluxo principal:**

1. O usuário seleciona a origem dos preços.
2. O provedor local carrega datas e preços por ativo.
3. O sistema valida datas, duplicidades, ordenação e valores.
4. As séries são alinhadas conforme política explícita.
5. Metadados registram fonte, frequência, intervalo, obtenção, observações e
   tratamento de ausências.
6. O sistema retorna séries válidas e problemas encontrados.

**Alternativas e falhas:** ativo ausente, histórico insuficiente, preço inválido,
data duplicada ou lacuna geram erro ou aviso conforme o impacto no cálculo.

**Critérios de aceitação:** o núcleo recebe um contrato de série, não um widget ou
caminho global; tratamento de missing values nunca é implícito.

## UC-05 — Configurar uma análise

**Objetivo:** selecionar parâmetros válidos e visíveis antes do cálculo.

**Pré-condições:** carteira e séries disponíveis.

**Fluxo principal:**

1. O usuário escolhe método de retorno, janela, horizonte e níveis de confiança
   dentre as opções suportadas na fase atual.
2. O sistema valida obrigatoriedade, domínio e consistência dos valores.
3. Uma síntese mostra os parâmetros efetivos.
4. O usuário confirma a configuração.

**Alternativas e falhas:** versão incompatível, confiança fora do intervalo,
janela não positiva ou combinação não suportada impede a execução e explica a
correção.

**Critérios de aceitação:** valores padrão são visíveis; a configuração que chega
ao núcleo é imutável ou tratada como valor; nenhuma opção visual cria uma regra
financeira própria.

## UC-06 — Executar analytics básicos

**Objetivo:** produzir medidas descritivas coerentes para a carteira.

**Pré-condições:** posições, preços e configuração válidos e dados suficientes.

**Fluxo principal:**

1. O sistema calcula valores de mercado e pesos.
2. Calcula a série de retornos da carteira conforme o método configurado.
3. Calcula volatilidade, drawdown e maximum drawdown.
4. Produz objetos de resultado com valor, unidade, período, parâmetros e avisos.
5. A interface apresenta a síntese sem recalcular as métricas.

**Alternativas e falhas:** denominador inválido, série constante, observações
insuficientes ou valores não finitos geram falha de domínio específica ou aviso
documentado.

**Critérios de aceitação:** pesos reconciliam com a convenção definida; resultados
de referência respeitam tolerâncias explícitas; não há dependência de PySide6.

## UC-07 — Executar risco histórico

**Objetivo:** estimar VaR e Expected Shortfall históricos sob uma configuração
explícita.

**Pré-condições:** série de retornos válida e observações suficientes.

**Fluxo principal:**

1. O sistema valida confiança, horizonte, janela e método de retorno.
2. Seleciona a amostra aplicável.
3. Calcula VaR histórico segundo a convenção de perda documentada.
4. Calcula Expected Shortfall sobre a cauda correspondente.
5. Retorna valores, convenção de sinal, amostra, parâmetros, hipóteses e avisos.

**Alternativas e falhas:** amostra insuficiente ou cauda vazia não retorna `NaN`
como sucesso; produz erro quantitativo explícito.

**Critérios de aceitação:** Expected Shortfall e VaR usam a mesma convenção;
casos pequenos podem ser verificados manualmente; escolhas de quantil e
escalonamento são documentadas antes da implementação.

## UC-08 — Interpretar e comparar resultados

**Objetivo:** compreender o significado e os limites dos números calculados.

**Pré-condições:** ao menos um resultado concluído.

**Fluxo principal:**

1. O sistema apresenta métricas, unidades e período.
2. O usuário consulta definição, método, parâmetros e hipóteses.
3. Avisos permanecem associados às métricas afetadas.
4. Quando dois modelos estiverem disponíveis, a comparação usa a mesma base ou
   explicita diferenças.

**Critérios de aceitação:** o painel não apresenta um valor de risco sem confiança,
horizonte e convenção; comparação incompatível é sinalizada.

## UC-09 — Exportar resultados básicos

**Objetivo:** salvar uma representação estruturada da análise.

**Pré-condições:** resultado disponível e destino gravável.

**Fluxo principal:**

1. O usuário escolhe um formato suportado e o destino.
2. O sistema reúne carteira, data-base, parâmetros, métricas, avisos, erros,
   versão e fonte dos dados disponíveis.
3. O exportador valida o conteúdo e grava o arquivo.
4. O sistema informa destino e conclusão.

**Alternativas e falhas:** destino inválido, permissão negada ou serialização
impossível preserva o resultado em memória e informa uma falha específica.

**Critérios de aceitação:** a exportação não recalcula métricas; um arquivo gerado
pode ser lido por teste de integração e reconciliado com o resultado original.

## Casos posteriores

### UC-10 — Salvar e reabrir projeto

Persistir carteira, referências de dados, configurações e estado compatível com
schema versionado. A reabertura valida versão e não mascara dados ausentes.

### UC-11 — Consultar histórico de execuções

Listar e abrir registros com identidade, versão, data, duração, entradas,
parâmetros, fonte, avisos, erros e resultados. O histórico não implica que os
arquivos externos originais ainda estejam disponíveis.

### UC-12 — Cancelar uma tarefa longa

Solicitar cancelamento cooperativo, manter a interface responsiva, liberar
recursos e distinguir cancelamento de falha. Resultados parciais não são tratados
como concluídos sem indicação explícita.

### UC-13 — Executar backtesting

Comparar P&L e VaR, identificar exceções e aplicar testes documentados. Hipóteses,
estatística, distribuição, p-valor e decisão devem acompanhar o resultado.

### UC-14 — Executar cenário de stress

Aplicar choques identificados e versionados, mostrar impacto total e por posição e
preservar unidades e fatores de risco. Cenários históricos exigem fontes e
metodologia documentadas.

## Rastreabilidade inicial

| Necessidade | Casos relacionados |
|---|---|
| entrada confiável | UC-02, UC-03, UC-04 |
| cálculo transparente | UC-05, UC-06, UC-07, UC-08 |
| reprodução e auditoria | UC-04, UC-05, UC-09, UC-10, UC-11 |
| interface responsiva | UC-01, UC-12 |
| evolução dos modelos | UC-07, UC-13, UC-14 |

## Pontos para revisão do autor

- A correção de dados ocorrerá dentro da aplicação ou apenas no arquivo de origem?
- O usuário poderá excluir conscientemente uma linha inválida e continuar?
- O preço informado na carteira é custo, preço de referência ou marcação atual?
- A exportação mínima precisa ser adequada para leitura humana, automação ou
  ambos?
