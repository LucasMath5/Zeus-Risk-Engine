# ADR-003 — Decimal, posições vendidas e convenções de pesos

- **Estado:** aceito
- **Data:** 2026-07-13
- **Decisores:** Lucas Silva
- **Escopo:** domínio de carteira e valoração básica

## Contexto

A Fase 2 introduz quantidade, preço, valor de mercado e pesos. Esses conceitos
parecem simples, mas ficam ambíguos quando há posições vendidas, exposição líquida
igual a zero ou instrumentos em moedas diferentes.

Usar `float` diretamente também pode introduzir artefatos binários antes mesmo de o
projeto chegar aos cálculos estatísticos. Por outro lado, arredondar automaticamente
todo valor para duas casas decimais destruiria informação válida de preços, frações de
cotas e quantidades.

O domínio precisa impedir que uma soma economicamente inválida seja apresentada como
resultado correto e, ao mesmo tempo, permanecer pequeno o suficiente para a fase atual.

## Decisão

### Representação numérica

Quantidade, preço, valor de mercado e pesos serão representados por `Decimal`.
Chamadores devem construir valores decimais a partir de texto ou inteiros, não de
`float`.

O domínio não aplica quantização ou arredondamento monetário automático. Escala de
exibição e regras específicas de liquidação pertencem a fases e contextos posteriores.
A precisão das divisões segue o contexto decimal ativo do Python; testes de razões
periódicas usam tolerância explícita.

### Quantidade e preço

- quantidade positiva representa posição comprada;
- quantidade negativa representa posição vendida;
- quantidade zero é inválida porque não representa exposição;
- quantidade e preço devem ser finitos;
- preço deve ser estritamente positivo.

### Moedas

Uma carteira pode conter mais de uma moeda, mas valores de moedas diferentes nunca são
somados implicitamente. A aplicação deve:

- solicitar uma moeda explicitamente; ou
- obter uma valoração separada por moeda.

Conversão para moeda-base só poderá ocorrer quando taxas, datas e política cambial forem
entradas explícitas e auditáveis.

### Valor de mercado

Para a posição `i`:

```text
V_i = q_i × p_i
```

onde `q_i` é a quantidade assinada e `p_i` é o preço positivo. Assim, `V_i` preserva o
sinal econômico da posição.

Para posições expressas na mesma moeda:

```text
N = Σ V_i
G = Σ |V_i|
```

`N` é o valor líquido e `G` é o valor bruto.

### Pesos

Duas bases são suportadas e sempre aparecem no resultado:

```text
w_i(net)   = V_i / N       quando N ≠ 0
w_i(gross) = |V_i| / G
```

Pesos líquidos preservam o sinal e somam aproximadamente 1, mas podem exceder 100% ou
ser negativos em carteiras long/short. Pesos brutos são não negativos e somam
aproximadamente 1. Pesos líquidos são rejeitados quando `N = 0`; o sistema não retorna
infinito, `NaN` ou um valor arbitrário.

### Identificação de duplicidades

Na fase atual, duas posições são duplicadas quando possuem o mesmo ticker normalizado e
a mesma moeda. Tickers iguais em moedas diferentes não são agregados. Quando `book`,
`strategy` ou identificadores de mercado forem introduzidos, essa chave deverá ser
reavaliada.

## Consequências positivas

- valores monetários simples não carregam artefatos binários de `float`;
- posições vendidas são representadas sem campo de direção duplicado;
- resultados não escondem a base de normalização;
- carteiras neutras continuam permitindo pesos brutos úteis;
- nenhuma taxa cambial é inventada;
- casos pequenos podem ser reconciliados manualmente.

## Consequências negativas e custos

- importadores precisarão converter texto para `Decimal` explicitamente;
- bibliotecas quantitativas baseadas em arrays usarão `float` em fases posteriores e
  exigirão uma fronteira de conversão documentada;
- divisões decimais periódicas ainda dependem de precisão e tolerância;
- consumidores precisam escolher entre base líquida e bruta;
- uma carteira multimoeda exige chamadas por moeda até existir conversão explícita.

## Alternativas consideradas

### `float` em todo o domínio

Rejeitado para preços e quantidades de entrada porque introduz representação binária
desnecessária nesta camada. `float` continua adequado a matrizes e estatística quando
essa escolha for documentada nas fases quantitativas.

### Inteiros em menor unidade monetária

Não adotado porque instrumentos podem ter escalas, moedas e quantidades fracionárias
diferentes. Uma única convenção de centavos seria insuficiente.

### Biblioteca externa de dinheiro

Adiada porque a Fase 2 necessita apenas de código de moeda e agregação controlada.
Adicionar uma dependência agora ampliaria o contrato sem caso de uso correspondente.

### Proibir carteiras multimoeda

Rejeitado porque limitaria desnecessariamente o modelo. A carteira pode preservar as
posições; somente a agregação incompatível é bloqueada.

### Somente peso líquido

Rejeitado porque falha em carteiras neutras e pode ocultar alavancagem. As duas bases
têm interpretações distintas e reais.

## Regras verificáveis

- `float`, `NaN`, infinito, quantidade zero e preço não positivo são rejeitados;
- posições vendidas produzem valor de mercado negativo;
- valor líquido é a soma assinada e valor bruto é a soma absoluta;
- pesos líquidos só existem com denominador líquido diferente de zero;
- pesos brutos são não negativos;
- agregação multimoeda sem filtro gera `CURRENCY_CONVERSION_REQUIRED`;
- resultados registram moeda e base de peso;
- nenhuma dependência externa é necessária para esses cálculos.

## Critério de reconsideração

A decisão deve ser revisada quando forem introduzidos conversão cambial, multiplicadores
de contrato, derivativos, ativos precificados por unidade não monetária ou arrays
quantitativos de grande volume. Uma mudança deve preservar a fronteira entre dados de
posição auditáveis e representação numérica de analytics.

## Relações

- [Modelo de domínio de carteira](../models/portfolio-domain.md)
- [Visão geral da arquitetura](../architecture/overview.md)
- [Glossário](../glossary.md)
