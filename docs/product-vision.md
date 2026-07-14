# Visão do produto

## Identificação

- **Produto:** Zeus Risk Engine
- **Aplicação:** Zeus Risk Engine
- **Pacote Python planejado:** `zeus_risk`
- **Versão inicial planejada:** 0.1.0
- **Author:** Lucas Silva
- **Licença planejada:** MIT
- **Estado deste documento:** proposta inicial para revisão

## Resumo executivo

O Zeus Risk Engine será uma aplicação desktop modular para importar, validar,
analisar e monitorar o risco de carteiras financeiras. O produto reunirá em um
único fluxo dados de posições, séries históricas, parâmetros de modelos,
resultados quantitativos e evidências de execução.

O sistema terá dois compromissos igualmente importantes:

1. oferecer um fluxo de análise útil, reproduzível e auditável; e
2. explicar os conceitos, hipóteses e limitações por trás dos resultados.

Ele não será apenas uma calculadora de VaR nem uma coleção de scripts. O núcleo
quantitativo será independente da interface, testável sem ambiente gráfico e
preparado para receber novos modelos e fontes de dados progressivamente.

## Problema que o produto resolve

Análises de risco construídas em planilhas e scripts isolados frequentemente
sofrem com entradas inconsistentes, parâmetros implícitos, resultados difíceis
de reproduzir e baixa rastreabilidade. Para estudantes e profissionais em
formação, existe ainda uma segunda dificuldade: muitas ferramentas mostram o
número final sem ensinar como ele foi obtido ou quando pode ser enganoso.

O Zeus Risk Engine pretende reduzir essas limitações por meio de:

- validação explícita das posições e dos dados de mercado;
- configurações versionadas e visíveis;
- resultados estruturados, acompanhados de interpretação e limitações;
- registro dos dados, parâmetros, avisos e versão utilizados em cada execução;
- separação entre regras quantitativas, coordenação da aplicação e interface;
- exemplos locais e sintéticos que não dependam de internet.

## Visão

> Ser uma referência educacional e de portfólio em engenharia de software
> aplicada a risco de mercado, permitindo que uma análise seja compreendida,
> reproduzida, testada e evoluída com segurança.

## Público-alvo

### Primário

- estudantes de finanças quantitativas e gestão de risco;
- analistas de risco, investimentos e Middle Office;
- profissionais de gestão de carteiras em busca de uma ferramenta didática;
- desenvolvedores interessados em sistemas financeiros testáveis.

### Necessidades do público

- importar uma carteira sem precisar alterar código;
- identificar erros antes de calcular métricas;
- entender parâmetros, fórmulas, hipóteses e convenções;
- comparar resultados de modelos de maneira consistente;
- produzir evidências que permitam repetir uma análise;
- aprender por meio de exemplos pequenos e verificáveis.

## Proposta de valor

O produto combina três qualidades que normalmente aparecem separadas:

- **rigor quantitativo:** fórmulas documentadas, tolerâncias explícitas e testes
  de regressão numérica;
- **engenharia profissional:** módulos coesos, contratos claros, testes
  automatizados e decisões arquiteturais registradas;
- **experiência didática:** resultados acompanhados de contexto, interpretação,
  hipóteses e limitações.

## Objetivos do produto

1. Conduzir o usuário por um fluxo completo, da importação à exportação de
   resultados.
2. Impedir que erros conhecidos de entrada sejam tratados como resultados
   válidos.
3. Tornar explícitos o modelo, a janela, o horizonte, a confiança, a fonte e o
   tratamento de dados de cada cálculo.
4. Permitir que o núcleo quantitativo seja executado e testado sem PySide6.
5. Oferecer resultados reproduzíveis com dados locais e configurações
   versionadas.
6. Evoluir em incrementos pequenos, cada um com documentação e critérios de
   aceitação verificáveis.

## Princípios de experiência

- **Clareza antes de densidade:** apresentar primeiro o resultado essencial e
  disponibilizar detalhes sob demanda.
- **Erro acionável:** informar o que ocorreu, onde ocorreu e como corrigir.
- **Aviso não é erro:** permitir continuidade quando o problema não invalida o
  cálculo, mantendo a advertência no resultado.
- **Sem números sem contexto:** toda métrica relevante deve identificar unidade,
  período, parâmetros e convenção.
- **Estados visíveis:** diferenciar vazio, carregando, concluído, cancelado,
  concluído com avisos e falha.
- **Reprodutibilidade por padrão:** evitar dependências externas nos exemplos
  básicos e registrar as entradas efetivamente usadas.

## Resultado mínimo valioso

A primeira versão funcional deverá permitir que uma pessoa:

1. inicie a aplicação;
2. importe uma carteira CSV;
3. revise erros e avisos de validação;
4. carregue preços de arquivos locais;
5. calcule pesos, retornos, volatilidade e drawdown;
6. calcule VaR histórico e Expected Shortfall;
7. consulte parâmetros e interpretação dos resultados;
8. exporte resultados básicos;
9. execute a suíte automatizada sem acesso à internet.

Esse resultado será entregue por várias fases; ele não faz parte isoladamente da
Fase 0.

## Critérios iniciais de sucesso

- cada fase possui critérios de conclusão e testes proporcionais ao seu risco;
- o fluxo mínimo pode ser executado a partir de uma instalação documentada;
- casos numéricos de referência produzem resultados dentro de tolerâncias
  declaradas;
- nenhuma fórmula financeira reside em widgets ou controladores da interface;
- erros de entrada são apresentados como problemas estruturados e identificados
  por códigos estáveis;
- uma execução futura pode informar versão, parâmetros, fonte, intervalo de
  dados, avisos, erros e hash das entradas;
- a documentação permite a outro desenvolvedor localizar responsabilidades e
  justificar as principais decisões.

## Restrições e premissas

- Python será a linguagem principal e PySide6 será usado na aplicação desktop.
- A primeira versão deve funcionar com dados locais e sem API externa
  obrigatória.
- O desenvolvimento será local e monousuário no escopo inicial.
- Precisão e transparência têm prioridade sobre quantidade de modelos.
- Dados de exemplo serão sintéticos ou públicos e não conterão credenciais ou
  informações confidenciais.
- Datas, convenções de retorno, moedas e unidades deverão ser explícitas nos
  contratos que as utilizarem.

## Não objetivos iniciais

Não fazem parte da primeira versão: autenticação, servidor web, nuvem, banco de
dados remoto, streaming em tempo real, integração com corretoras, envio de
ordens, otimização de portfólio, inteligência artificial, múltiplos usuários e
microserviços. A lista completa e as fronteiras de evolução estão em
[Escopo](scope.md).

## Uso responsável

O Zeus Risk Engine destina-se a fins educacionais, de pesquisa e de portfólio.
Ele não constitui aconselhamento financeiro e não deve ser usado como única base
para decisões de investimento ou de gestão de risco. Resultados quantitativos
dependem da qualidade dos dados, das hipóteses do modelo e da adequação dos
parâmetros ao contexto analisado.

## Pontos para revisão do autor

- O público primário está priorizado corretamente?
- O resultado mínimo cobre o fluxo que deve aparecer primeiro no portfólio?
- Existe alguma instituição, classe de ativo ou mercado que deva ser
  explicitamente priorizado ou excluído?
- Quais evidências serão mais importantes na apresentação profissional: vídeo,
  screenshots, relatório exportado ou estudo de caso reproduzível?
- Os critérios de sucesso são verificáveis e compatíveis com o tempo disponível?
