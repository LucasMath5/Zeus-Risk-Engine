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
| 0 | planejamento e especificação | nenhuma | visão, escopo, casos, glossário, arquitetura, roadmap e ADRs revisáveis | em revisão |
| 1 | fundação do repositório | Fase 0 | pacote instalável, CLI mínima, metadados, qualidade e testes básicos | planejada |
| 2 | domínio de carteira | Fase 1 | instrumentos, posições, carteira, validações, valor e pesos testados | planejada |
| 3 | importação CSV | Fase 2 | normalização, parsing, problemas por linha e fixture de exemplo | planejada |
| 4 | importação XLSX | Fase 3 | seleção de planilha e mapeamento integrados à mesma validação | planejada |
| 5 | dados de mercado locais | Fases 2–3 | port, provider CSV, séries, metadados, alinhamento e cache testados | planejada |
| 6 | analytics básicos | Fases 2 e 5 | retornos, volatilidade, correlação, drawdown e concentração documentados | planejada |
| 7 | VaR histórico | Fase 6 | configuração, convenção, quantil, resultado e testes numéricos | planejada |
| 8 | Expected Shortfall | Fase 7 | cauda, comparação com VaR, documentação e testes | planejada |
| 9 | interface inicial | Fases 3 e 6–8 | importação, validação, posições e resultados em PySide6 | planejada |
| 10 | projetos e configurações | Fase 9 | salvar/carregar e JSON com schema validado | planejada |
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

O autor deve confirmar público prioritário, suporte inicial a posições vendidas,
moeda-base, classe de ativo dos exemplos, formato mínimo de exportação e sistemas
operacionais pretendidos. Essas respostas refinam fases futuras, mas não impedem
a fundação genérica da Fase 1.

## Próxima etapa recomendada — Fase 1

### Objetivo

Criar uma fundação pequena e executável que prove instalação, importação do
pacote, versionamento, CLI e ferramentas de qualidade, sem antecipar modelos de
domínio.

### Funcionalidades incluídas

- layout `src/zeus_risk` e versão 0.1.0;
- ponto de entrada CLI mínimo com nome e versão;
- `pyproject.toml` com metadados e grupos de desenvolvimento justificados;
- README inicial, licença MIT, changelog e guia de contribuição;
- pytest, Ruff e type checking configurados de maneira gradual;
- primeiro teste de instalação/importação e teste da CLI;
- workflow de CI mínimo após os comandos locais estarem estáveis.

### Arquivos previstos

```text
src/zeus_risk/__init__.py
src/zeus_risk/__main__.py
src/zeus_risk/cli.py
tests/unit/test_package.py
tests/integration/test_cli.py
pyproject.toml
README.md
LICENSE
CHANGELOG.md
CONTRIBUTING.md
.gitignore
.github/workflows/quality.yml
```

A lista poderá ser reduzida se um arquivo não tiver responsabilidade real na
etapa. A decisão por PySide6 já está registrada, mas a biblioteca só deve ser
declarada quando a primeira integração gráfica realmente a utilizar.
Dependências quantitativas também só entram quando usadas.

### Decisões a fechar na Fase 1

- versão mínima de Python e matriz de CI;
- ferramenta de build e metadados PEP 621;
- Ruff como lint/formatter ou Ruff com Black;
- mypy ou Pyright;
- convenção de changelog e versionamento;
- nome e comportamento exato do comando CLI.

### Critérios de saída previstos

- instalação editável documentada em ambiente limpo;
- `python -m zeus_risk --version` ou comando equivalente funciona;
- lint, format check, type check e testes passam localmente;
- a pipeline executa os mesmos comandos;
- README explica instalar, executar, testar, roadmap, autor, licença e aviso de
  uso educacional;
- nenhum módulo financeiro vazio é criado.

### Testes previstos

- pacote expõe `__version__ == "0.1.0"`;
- CLI retorna código zero e mostra nome/versão;
- importação do core futuro não exige Qt — a regra começa simples e será ampliada;
- smoke test da instalação configurada.

### Commit sugerido para a Fase 1

```text
chore: establish Python package and quality tooling
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
