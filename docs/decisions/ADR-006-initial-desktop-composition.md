# ADR-006 — Composição desktop inicial

- **Estado:** aceito
- **Data:** 2026-07-16
- **Decisores:** Lucas Silva
- **Escopo:** composição e execução do primeiro fluxo PySide6

## Contexto

As Fases 3–8 entregaram importadores, dados locais, analytics, VaR e Expected
Shortfall sem interface. A Fase 9 precisa expor esse caminho em desktop sem repetir
validações nos widgets, contaminar o core com Qt ou antecipar a infraestrutura de
projetos, workers e persistência.

## Decisão

Usar uma janela Qt Widgets com duas abas sequenciais: carteira/validação e risco
histórico. `MainWindow` mantém apenas o estado efêmero da sessão e traduz eventos e
falhas. `PortfolioRiskWorkflow`, no pacote `application`, compõe os adapters e as
funções quantitativas sem importar PySide6.

Posições e problemas são apresentados por subclasses somente leitura de
`QAbstractTableModel`. As views recebem `ImportResult` ou `HistoricalRiskAnalysis` e
apenas formatam os valores; retornos, pesos, VaR e ES continuam no core. Falhas
esperadas preservam o código de `ValidationIssue` em banners não modais.

O fluxo da Fase 9 é síncrono e limitado a arquivos locais pequenos. O botão de
execução fica bloqueado durante a chamada. Operações classificadas como demoradas
serão movidas para workers canceláveis na Fase 14, mantendo o mesmo caso de uso
síncrono testável.

O bootstrap oferece `zeus-risk-gui` e `python -m zeus_risk.app`, reutiliza uma
`QApplication` existente nos testes, aplica o estilo Fusion e um stylesheet contido.
Os testes usam `QT_QPA_PLATFORM=offscreen` e não entram no event loop principal.

## Consequências

- o primeiro caminho do usuário é executável sem terminal após a inicialização;
- a direção `app -> application -> domain/core/adapters` permanece verificável;
- os modelos de tabela escalam melhor e preservam dados imutáveis;
- o estado ainda não sobrevive ao encerramento da aplicação;
- arquivos grandes podem bloquear temporariamente a UI até a Fase 14;
- a interface não oferece edição, gráficos, exportação nem histórico nesta fase.

A limitação de estado em memória descrita acima foi posteriormente atendida pelo
[ADR-007](ADR-007-versioned-project-json.md) na Fase 10; os demais limites permanecem.

## Alternativas consideradas

### Cálculo diretamente na janela

Rejeitado porque duplicaria regras, reduziria a cobertura independente de GUI e
violaria o ADR-001.

### Wizard modal

Rejeitado nesta fase porque esconderia resultados anteriores e dificultaria revisar
problemas e parâmetros lado a lado. As abas preservam contexto com menos estado.

### Workers desde o primeiro fluxo

Adiado porque os exemplos são pequenos e a Fase 14 já define progresso, cancelamento
e encerramento seguro. Antecipá-los aumentaria o ciclo de vida Qt antes de existir uma
tarefa pesada medida.

### Modelos baseados em `QTableWidget`

Rejeitados para posições e problemas: duplicariam estado por célula e tornariam menos
clara a adaptação dos resultados imutáveis.

## Regras verificáveis

- `application`, `domain` e `core` não importam PySide6;
- widgets não chamam funções de cálculo financeiro;
- o botão de análise exige carteira sem erros e caminho de preços;
- falhas conhecidas mantêm códigos estruturados visíveis;
- models são somente leitura e usam o protocolo de reset do Qt;
- testes GUI executam offscreen, sem rede e sem diálogos interativos;
- o resultado mostra unidade, método, parâmetros, amostra, cauda e data-base.

## Referências

- [Qt for Python — Getting Started](https://doc.qt.io/qtforpython-6/gettingstarted.html)
- [Qt for Python — QAbstractTableModel](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractTableModel.html)
- [PySide6 no PyPI](https://pypi.org/project/PySide6/)
- [ADR-001 — Separação entre interface e núcleo](ADR-001-separation-of-ui-and-core.md)
- [ADR-002 — Uso de PySide6](ADR-002-use-of-pyside6.md)
- [Roadmap](../development/roadmap.md)
