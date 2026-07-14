# ADR-002 — Uso de PySide6 na aplicação desktop

- **Estado:** aceito
- **Data:** 2026-07-13
- **Decisores:** Lucas Silva
- **Escopo:** tecnologia da interface desktop

## Contexto

O Zeus Risk Engine precisa de uma interface desktop profissional capaz de
apresentar tabelas de posições, painéis de validação, formulários de parâmetros,
gráficos, progresso e tarefas canceláveis. O projeto também pretende demonstrar
engenharia de uma aplicação Python distribuível e manter o motor quantitativo
independente da apresentação.

A tecnologia escolhida deve oferecer componentes desktop maduros, model/view
para dados tabulares, sinais e slots, suporte a tarefas em background,
acessibilidade e recursos para empacotamento. A escolha é uma restrição de
produto definida pelo autor, mas suas consequências precisam permanecer
explícitas.

## Decisão

Usar **PySide6** como binding Qt da aplicação desktop.

PySide6 ficará confinado ao pacote de apresentação e ao ponto de composição. O
core, o domínio, importadores, providers, repositories e cálculos não importarão
Qt. Models, signals, slots, threads e recursos Qt serão introduzidos somente nas
fases que possuírem fluxos de interface reais.

A interface seguirá estas orientações:

- preferir model/view para tabelas a criar um widget completo por célula;
- usar layouts e componentes reutilizáveis em vez de posições fixas;
- manter lógica de estado em controllers/presenters pequenos;
- executar casos de uso demorados por workers com cancelamento cooperativo;
- não acessar widgets a partir da thread de trabalho;
- separar recursos visuais de regras de negócio;
- disponibilizar estados vazio, carregando, sucesso, aviso, erro e cancelado;
- tornar fluxos principais navegáveis por teclado e não depender apenas de cor;
- verificar requisitos de licença e distribuição novamente antes do release.

## Consequências positivas

- conjunto amplo de widgets e padrões desktop maduros;
- suporte adequado a tabelas grandes via model/view;
- mecanismo de sinais e slots apropriado para eventos e progresso;
- possibilidade de aparência consistente e recursos de acessibilidade;
- integração natural com o ecossistema Qt para gráficos e empacotamento futuro;
- experiência relevante para um portfólio de aplicação Python profissional.

## Consequências negativas e custos

- dependência de distribuição significativamente maior que uma CLI;
- testes GUI requerem configuração específica no ambiente local e no CI;
- ciclo de vida de `QApplication`, threads e objetos Qt possui regras próprias;
- empacotamento e plugins de plataforma precisam de smoke tests por sistema;
- atualização de versões do Qt pode alterar comportamento visual ou de build;
- a liberdade visual do Qt pode incentivar customização excessiva e difícil de
  manter.

Esses custos serão reduzidos mantendo poucos componentes customizados, testando
o core fora do Qt, introduzindo testes GUI proporcionais e validando builds em
ambientes explicitamente suportados.

## Alternativas consideradas

### Tkinter

Possui distribuição simples em muitos ambientes Python, mas foi rejeitado para o
produto por oferecer uma base menos adequada ao conjunto planejado de tabelas,
model/view, estados complexos e acabamento desktop.

### PyQt6

Oferece API Qt equivalente em muitos aspectos. Não foi escolhido porque PySide6
é a tecnologia definida para o projeto. Questões de licença, suporte e
distribuição serão reavaliadas antes de releases, independentemente do binding.

### Aplicação web local

Poderia facilitar layouts e visualização, mas exigiria servidor ou runtime web e
mudaria o objetivo de demonstrar uma aplicação desktop PySide6. Permanece fora do
escopo inicial.

### CLI como interface única

Continuará útil para smoke tests e automação, mas não atende o objetivo de fluxo
visual para revisão de posições, problemas e resultados.

## Regras verificáveis

- `PySide6` não aparece nas dependências importadas por `domain` ou `core`;
- testes quantitativos não criam aplicação Qt;
- sinais carregam resultados estruturados ou identificadores, não executam
  fórmulas em slots visuais;
- operações classificadas como demoradas não bloqueiam o event loop;
- testes cobrem transições de estado e models de tabela prioritários;
- o processo de build inclui smoke test de inicialização nos ambientes
  oficialmente suportados;
- a interface exibe versão e aviso de uso educacional em local apropriado.

## Impacto nas fases

- Fase 1 registra a dependência e prepara pontos de entrada, sem exigir janela.
- Fase 9 cria a primeira interface sobre casos de uso já testados.
- Fase 14 formaliza workers, progresso, cancelamento e encerramento seguro.
- Fase 19 valida empacotamento, plugins Qt, recursos e instalador.

## Critério de reconsideração

A escolha pode ser revista antes de uma versão estável se testes demonstrarem
impedimento de distribuição, acessibilidade ou suporte nos ambientes-alvo. Uma
mudança exige novo ADR que substitua este, plano de migração e preservação da
independência definida no ADR-001.

## Relações

- [Visão geral da arquitetura](../architecture/overview.md)
- [ADR-001 — Separação entre interface e núcleo](ADR-001-separation-of-ui-and-core.md)
- [Roadmap](../development/roadmap.md)
