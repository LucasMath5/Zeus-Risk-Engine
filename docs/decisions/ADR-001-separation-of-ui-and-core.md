# ADR-001 — Separação entre interface e núcleo quantitativo

- **Estado:** aceito
- **Data:** 2026-07-13
- **Decisores:** Lucas Silva
- **Escopo:** arquitetura da aplicação

## Contexto

O Zeus Risk Engine será uma aplicação desktop, mas seu principal valor está nas
regras de validação, nos modelos de carteira e nos cálculos estatísticos e
financeiros. Colocar essas regras em widgets, handlers de sinais ou classes Qt
dificultaria:

- testes rápidos e determinísticos;
- verificação matemática isolada;
- execução sem ambiente gráfico;
- reutilização por CLI, scripts ou relatórios;
- substituição e evolução da interface;
- compreensão das responsabilidades por pessoas em aprendizado.

Ao mesmo tempo, criar serviços distribuídos ou uma arquitetura excessivamente
genérica adicionaria custo sem resolver um problema presente.

## Decisão

O projeto adotará um monólito modular com separação explícita entre:

1. **domínio e core quantitativo**, que contêm modelos, invariantes, validações e
   cálculos financeiros/estatísticos;
2. **camada de aplicação**, que coordena casos de uso e define ports necessários;
3. **adapters e infraestrutura**, que tratam arquivos, mercado, persistência,
   exportação e serviços técnicos; e
4. **aplicação desktop PySide6**, que coleta entradas, aciona casos de uso e
   apresenta estados e resultados.

O núcleo não pode importar PySide6 nem depender de widgets, event loop, sinais ou
threads Qt. A interface não pode implementar fórmulas financeiras, regras de
validação de domínio ou recálculo de resultados.

Casos de uso do núcleo e da aplicação serão síncronos por padrão. Workers Qt
encapsularão esses casos quando uma operação precisar sair da thread da UI.
Dependências externas serão acessadas por contratos pequenos definidos pelo lado
consumidor e injetadas no ponto de composição.

## Regras verificáveis

- módulos em `domain` e `core` não importam nada de `app`;
- testes unitários do core executam sem criar `QApplication`;
- fechar uma view não altera o resultado de um cálculo em andamento, exceto por
  cancelamento cooperativo explícito;
- views recebem objetos de resultado e apenas os formatam;
- importadores, providers e repositories não são encontrados por estado global;
- exceções tecnológicas são traduzidas em fronteiras conhecidas sem perder a
  causa para diagnóstico;
- uma regra de dependência automatizada poderá ser adicionada quando a estrutura
  física existir.

## Consequências positivas

- fórmulas e validações podem ser testadas rapidamente e com casos manuais;
- falhas de UI não contaminam o modelo quantitativo;
- a mesma capacidade pode ser usada por GUI, CLI ou teste;
- fontes de dados e persistência podem evoluir sem alterar cálculos;
- processamento assíncrono permanece uma preocupação de coordenação;
- a organização serve como exemplo didático de direção de dependências.

## Consequências negativas e custos

- haverá código de adaptação entre objetos internos e models/widgets Qt;
- disciplina é necessária para evitar duplicação de validação na interface;
- alguns conceitos simples atravessarão uma camada de aplicação adicional;
- contratos mal escolhidos podem criar abstração prematura;
- mapeamento de erros técnicos para mensagens de usuário exige trabalho explícito.

Os custos serão controlados criando ports apenas para casos de uso reais e
preferindo funções, dataclasses e protocolos pequenos a frameworks arquiteturais.

## Alternativas consideradas

### Lógica diretamente nos widgets

Rejeitada porque acopla cálculo ao ciclo de vida da interface, exige ambiente Qt
nos testes e incentiva duplicação entre telas.

### MVC Qt como arquitetura de todo o sistema

Rejeitada como limite principal. Models/views do Qt são úteis na apresentação,
mas não representam adequadamente o domínio quantitativo nem as fronteiras de
arquivos e persistência.

### Microserviços ou backend separado

Rejeitados no escopo inicial por aumentarem implantação, comunicação, observação
e consistência sem requisito de escala, rede ou múltiplos usuários.

### Framework completo de injeção de dependência

Não adotado inicialmente. Composição manual é suficiente e mantém os contratos
visíveis. A decisão pode ser revista se a montagem se tornar um problema medido.

## Impacto nas fases

- Fase 1 cria apenas o pacote e pontos de entrada mínimos.
- Fase 2 estabelece domínio sem Qt.
- Fases 3–8 implementam adapters e core antes da interface.
- Fase 9 integra capacidades já testadas ao PySide6.
- Fase 14 envolve casos de uso existentes em workers, sem reescrever as fórmulas.
- Fases 16–17 adicionam persistência e exportação atrás de fronteiras próprias.

## Critério de reconsideração

Esta decisão deve ser revisada se surgir requisito comprovado de execução remota,
múltiplos processos, colaboração multiusuário ou implantação independente do
motor. Mesmo nesse caso, a independência do core continua desejável; o que pode
mudar é a fronteira de processo.

## Relações

- [Visão geral da arquitetura](../architecture/overview.md)
- [ADR-002 — Uso de PySide6](ADR-002-use-of-pyside6.md)
- Uma ADR futura formalizará convenção de sinal de risco.
