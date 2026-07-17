# Primeiro fluxo desktop

Este tutorial executa o fluxo real da Fase 9 com dados pequenos, sintéticos e locais.
Ele não acessa rede e não deve ser interpretado como recomendação financeira.

## 1. Instalar e iniciar

Na raiz do repositório, crie e ative um ambiente virtual e instale o projeto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
zeus-risk-gui
```

Também é possível iniciar com `python -m zeus_risk.app`.

## 2. Importar a carteira

Na aba **Carteira**, escolha **Importar carteira** e abra:

```text
assets/samples/risk_portfolio.csv
```

A tela deve mostrar duas linhas aceitas, zero erros e as posições `ZEUS_EQ1` e
`ZEUS_EQ2`. Para XLSX com mais de uma planilha, o sistema solicita explicitamente a
worksheet antes da importação.

## 3. Selecionar preços e parâmetros

Na aba **Risco histórico**, escolha **Selecionar preços** e abra:

```text
assets/samples/market_prices.csv
```

O exemplo contém três preços por ativo e, portanto, apenas dois retornos diários.
Configure:

- confiança: `50,0%`;
- horizonte: `1 dia`;
- janela: `2 cenários`.

A configuração pequena existe apenas para tornar o exemplo verificável. Os padrões de
95%, um dia e 252 cenários exigem uma série histórica compatível.

## 4. Executar e revisar

Escolha **Executar análise**. A aplicação percorre o provider CSV local, alinhamento
por interseção, retornos simples da carteira, VaR histórico e Expected Shortfall.

O resultado mostra VaR, ES, método, unidade relativa, confiança, horizonte, janela,
intervalo da amostra, quantidade de observações na cauda e data de referência. Com
estes arquivos, o VaR exibido é `0,0000%`; o ES permanece positivo porque o pior dos
dois cenários é uma perda.

## Falhas úteis para revisão

- Manter confiança em 95% e janela em 2 produz
  `INSUFFICIENT_VAR_TAIL_OBSERVATIONS`.
- Selecionar uma carteira com linha inválida mantém o código, a mensagem, o campo e a
  linha no painel e bloqueia a execução dependente.
- Selecionar preços sem todos os tickers produz uma falha estruturada; nenhuma série é
  preenchida silenciosamente.

## Continuação do fluxo

Depois de concluir a análise, use o
[tutorial de projetos](save-and-reopen-project.md) para salvar e reabrir entradas e
parâmetros. Workers e cancelamento pertencem à Fase 14; exportação, histórico e
relatórios continuam fora deste fluxo.
