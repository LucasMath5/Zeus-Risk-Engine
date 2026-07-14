# Escopo

## Finalidade

Este documento define as fronteiras do Zeus Risk Engine e diferencia:

- o trabalho documental da Fase 0;
- o escopo da primeira versão funcional;
- capacidades planejadas para fases posteriores; e
- itens deliberadamente fora do escopo inicial.

Alterações relevantes nessas fronteiras devem ser registradas no roadmap e,
quando envolverem uma decisão estrutural, em um ADR.

## Escopo da Fase 0 — Planejamento e especificação

### Incluído

- visão do produto, público-alvo e proposta de valor;
- escopo inicial e não objetivos;
- atores e casos de uso do fluxo principal;
- glossário de produto, risco e engenharia;
- arquitetura lógica e proposta incremental de repositório;
- roadmap por fases e critérios de passagem;
- decisão de separar interface e núcleo;
- decisão de utilizar PySide6.

### Não incluído

- código Python, pacote instalável ou CLI;
- interface gráfica ou wireframes executáveis;
- modelos de domínio implementados;
- importação CSV ou XLSX;
- cálculos financeiros ou estatísticos;
- persistência, cache ou relatórios;
- configuração de ferramentas e dependências.

### Critério de conclusão

A fase termina quando os oito documentos iniciais existem, não se contradizem e
permitem revisar propósito, limites, responsabilidades arquiteturais, sequência
de entrega e decisões já aceitas.

## Escopo da primeira versão funcional

### Fluxo principal incluído

1. Iniciar a aplicação desktop.
2. Importar uma carteira em CSV.
3. Normalizar colunas e validar as posições.
4. Exibir linhas válidas, avisos e erros sem encerrar inesperadamente.
5. Carregar séries de preços de arquivos locais.
6. Alinhar dados e informar o tratamento de valores ausentes.
7. Calcular valor de mercado e pesos da carteira.
8. Calcular retornos, volatilidade e drawdown.
9. Calcular VaR histórico e Expected Shortfall com parâmetros explícitos.
10. Apresentar resultados, interpretação, hipóteses e limitações.
11. Exportar resultados básicos em pelo menos um formato estruturado.
12. Executar testes unitários, de integração e de regressão numérica relevantes.

### Dados de posição iniciais

| Campo | Obrigatoriedade inicial | Regra conceitual |
|---|---:|---|
| `ticker` | obrigatório | identificador não vazio e normalizado |
| `quantity` | obrigatório | número finito; sinal representa posição comprada ou vendida |
| `price` | obrigatório | número finito e estritamente positivo |
| `asset_class` | obrigatório | valor pertencente à taxonomia suportada |
| `currency` | obrigatório | código de moeda reconhecido pela aplicação |
| `sector` | opcional | texto normalizado; ausência pode gerar aviso |

A obrigatoriedade e os valores permitidos serão fechados na fase de modelagem do
domínio. `book`, `strategy`, `country`, `issuer`, `rating`, `benchmark`,
`maturity` e sensibilidades ficam planejados, sem implementação antecipada.

### Dados de mercado iniciais

- arquivos locais como fonte obrigatória da primeira versão funcional;
- provedor de demonstração opcional, desde que determinístico;
- frequência inicialmente diária;
- identificação de ativo, fonte, período, obtenção, observações e tratamento de
  ausências;
- nenhuma chamada externa durante testes unitários ou exemplos básicos.

### Métricas iniciais

- valor de mercado por posição e total;
- pesos;
- exposição líquida e bruta quando compatível com as posições suportadas;
- retornos simples ou logarítmicos conforme configuração;
- volatilidade com frequência e anualização explícitas;
- drawdown e maximum drawdown;
- VaR histórico;
- Expected Shortfall histórico.

As definições matemáticas, convenções de sinal, métodos de quantil e casos-limite
serão documentados nas fases em que cada cálculo for implementado.

### Interface inicial

- janela principal;
- fluxo de importação CSV;
- tabela de posições;
- painel de validação;
- configuração mínima dos cálculos disponíveis;
- painel básico de resultados;
- feedback para vazio, processamento, conclusão, aviso e erro.

## Requisitos não funcionais iniciais

### Correção e testabilidade

- núcleo quantitativo sem dependência de PySide6;
- type hints nas interfaces públicas;
- objetos estruturados para entradas, problemas e resultados;
- tolerâncias numéricas explícitas nos testes;
- resultados determinísticos quando houver seed ou dados fixos.

### Reprodutibilidade e auditoria

- parâmetros efetivos e versão do software associados ao resultado;
- fonte e intervalo de dados identificáveis;
- avisos e erros preservados;
- configurações exportáveis e versionadas quando essa capacidade for entregue;
- hash de entradas e registro persistente em fases posteriores.

### Usabilidade e acessibilidade

- mensagens em linguagem compreensível e com ação sugerida;
- navegação utilizável por teclado nos fluxos principais;
- informação não transmitida apenas por cor;
- tarefas longas sem congelar a interface quando os workers forem introduzidos;
- unidades, datas e convenções sempre visíveis.

### Manutenibilidade

- responsabilidades separadas por camada;
- dependências adicionadas apenas com necessidade demonstrada;
- decisões estruturais registradas em ADRs;
- documentação atualizada na mesma mudança que alterar comportamento relevante.

### Portabilidade

O primeiro ambiente-alvo será desktop. Os sistemas operacionais efetivamente
suportados e o processo de empacotamento serão definidos após testes na fase de
distribuição; a arquitetura não deve presumir um instalador específico antes
disso.

## Capacidades planejadas depois do primeiro fluxo

- importação XLSX e mapeamento de colunas;
- configurações e projetos persistentes;
- VaR paramétrico normal e EWMA;
- backtesting com Kupiec, Christoffersen e traffic light;
- stress testing hipotético e, com fontes adequadas, histórico;
- persistência SQLite e histórico de execuções;
- relatórios CSV, XLSX, JSON, HTML e PDF;
- Monte Carlo correlacionado e análise de convergência;
- decomposição e contribuição de risco;
- registro interno de novos modelos.

Planejado não significa aprovado para implementação imediata. Cada capacidade
entra no produto apenas em sua fase, com critérios e testes próprios.

## Fora do escopo inicial

- autenticação e autorização;
- aplicação web, servidor ou API pública;
- armazenamento em nuvem ou banco de dados remoto;
- dados em streaming e baixa latência;
- conexão com corretoras e execução de ordens;
- recomendação de investimento;
- otimização de portfólio;
- inteligência artificial;
- colaboração ou múltiplos usuários;
- microserviços;
- precificação completa de derivativos;
- risco de crédito, liquidez e operacional como módulos completos;
- certificação regulatória ou uso como sistema oficial de produção.

## Dependências e restrições de sequência

- modelos quantitativos dependem de domínio e contratos de dados estáveis;
- a importação depende das regras de validação do domínio;
- analytics dependem de séries alinhadas e políticas de missing values;
- a interface consome casos de uso já testados, não define regras financeiras;
- persistência depende de contratos que tenham demonstrado estabilidade;
- relatórios dependem de resultados e metadados estruturados;
- empacotamento vem após o fluxo funcional e sua suíte de testes.

## Gestão de mudanças de escopo

Uma proposta de mudança deve responder:

1. qual problema do usuário resolve;
2. em qual fase entra e de que depende;
3. quais contratos ou decisões altera;
4. quais testes demonstram sua conclusão;
5. quais itens existentes deixam de ser prioridade.

Mudanças pequenas podem atualizar este documento e o roadmap. Mudanças que
alterem limites de camada, tecnologia principal, persistência, convenções
quantitativas ou compatibilidade exigem um ADR novo ou a substituição explícita
de um ADR existente.

## Pontos para revisão do autor

- Como o CSV deve distinguir uma posição vendida válida de um sinal digitado por engano?
- A primeira versão deve tratar apenas uma moeda-base ou converter moedas?
- Qual será o primeiro formato de exportação: CSV, JSON ou ambos?
- Quais sistemas operacionais devem ser oficialmente suportados no portfólio?
- Há uma classe de ativo prioritária para os exemplos iniciais?
