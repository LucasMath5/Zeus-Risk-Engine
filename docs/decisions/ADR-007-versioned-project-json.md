# ADR-007 — Projeto JSON versionado e referencial

- **Estado:** aceito
- **Data:** 2026-07-16
- **Decisores:** Lucas Silva
- **Escopo:** persistência mínima do fluxo desktop da Fase 10

## Contexto

A Fase 9 mantém carteira, caminho de preços e parâmetros apenas em memória. A primeira
persistência precisa permitir reabrir esse estado sem antecipar SQLite, histórico de
execuções, migrações complexas ou armazenamento opaco de dados financeiros.

## Decisão

Adotar um JSON UTF-8 com extensão recomendada `*.zeus.json` e `schema_version` igual a
`1.0`. O contrato imutável `DesktopProject` contém nome, referências à carteira e aos
preços, worksheet, `HistoricalVaRConfiguration` e `ReturnMethod`.

O arquivo é **referencial**: não copia posições, preços ou resultados. Referências
dentro da pasta do projeto são relativas; externas permanecem absolutas. O adapter
`JsonProjectStore` aplica limite de tamanho, campos exatos, detecção de duplicatas,
tipos estritos, revalidação do domínio e gravação atômica. O nível de confiança é uma
string decimal.

`ProjectWorkflow` cria o snapshot e coordena o store. A janela apenas coleta o estado,
traduz `ProjectFileError` e indica alterações não salvas por `*` no título.

## Consequências

- projetos pequenos podem ser revisados e versionados como texto;
- referências relativas permitem mover uma árvore autocontida;
- dados financeiros não são duplicados sem consentimento;
- alterar ou remover um arquivo referenciado impede a restauração completa;
- caminhos absolutos reduzem portabilidade quando os dados ficam fora da pasta;
- schemas desconhecidos falham até existir uma migração explícita;
- resultados não são persistidos nesta fase e devem ser recalculados.

## Alternativas consideradas

### Incorporar carteira e preços no JSON

Rejeitado porque duplicaria dados potencialmente confidenciais, aumentaria o arquivo e
criaria conflito entre cópia incorporada e fonte original.

### SQLite na Fase 10

Adiado para a Fase 16, quando projetos, execuções e histórico justificarem repository,
migrações e transações de banco.

### Aceitar campos desconhecidos

Rejeitado porque erros de digitação poderiam alterar silenciosamente a configuração
efetiva. Evolução compatível será decidida por versão do schema, não por descarte.

### Gravação direta no destino

Rejeitada porque uma interrupção poderia truncar o único arquivo do usuário. O adapter
grava e sincroniza um temporário na mesma pasta antes de substituí-lo.

## Regras verificáveis

- abrir o mesmo projeto resolve os mesmos arquivos independentemente do diretório atual;
- o round trip preserva configuração e método exatamente;
- campos ausentes, extras, duplicados e tipos incorretos produzem códigos estruturados;
- referências ausentes não são mascaradas;
- falha de gravação não é apresentada como sucesso;
- widgets não fazem parsing ou serialização JSON;
- abrir um projeto inválido não substitui parcialmente o estado atual da janela.

## Relações

- [Formato de projeto desktop](../models/project-file.md)
- [ADR-001 — Separação entre interface e núcleo](ADR-001-separation-of-ui-and-core.md)
- [ADR-006 — Composição desktop inicial](ADR-006-initial-desktop-composition.md)
- [Roadmap](../development/roadmap.md)
