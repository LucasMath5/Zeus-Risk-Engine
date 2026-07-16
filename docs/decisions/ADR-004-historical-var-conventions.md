# ADR-004 — Convenções do VaR histórico

- **Estado:** aceito
- **Data:** 2026-07-16
- **Decisor:** Lucas Silva
- **Escopo:** Fase 7 — Value at Risk histórico

Esta decisão é complementada pelo ADR-005 para a definição da cauda do Expected
Shortfall; suas convenções de VaR permanecem vigentes.

## Contexto

VaR histórico depende de escolhas que podem produzir números diferentes sobre a mesma
série: sinal da perda, quantil, interpolação, formação do horizonte, seleção da janela,
resolução mínima da cauda e unidade monetária ou relativa. Ocultar qualquer uma delas
reduziria a auditabilidade do motor.

A Fase 6 já fornece `ReturnSeries` simples ou logarítmica, diária, cronológica,
imutável e calculada com `Decimal`. A Fase 7 deve usar esse contrato sem introduzir
arquivos, interface, câmbio, Expected Shortfall ou uma abstração prematura de vários
modelos.

## Decisão

### Sinal e apresentação

Cada cenário usa `loss = -return`: perda tem sinal positivo e ganho, negativo. O
quantil empírico bruto é preservado como `quantile_loss`; o VaR apresentado é
`max(quantile_loss, 0)`. Assim, ganho no quantil não vira risco negativo nem uma
magnitude positiva enganosa.

### Quantil

O método inicial é nearest-rank sem interpolação. Para `w` perdas ordenadas e
confiança `c`, o rank de base 1 é `ceil(c * w)`. O valor é a observação nesse rank.
A configuração registra `nearest_rank`; novos métodos exigirão enum, documentação e
testes próprios.

### Resolução mínima

A janela deve satisfazer `w >= ceil(1 / (1 - c))`. Isso mantém ao menos uma
observação além do rank. Uma série menor falha explicitamente; o motor não diminui a
confiança, completa a cauda nem inventa um quantil.

### Horizonte e janela

O horizonte é formado por blocos móveis sobrepostos. Retornos simples são compostos
geometricamente e log-retornos são somados. Não se usa regra da raiz do tempo. A janela
seleciona os cenários de horizonte mais recentes depois da agregação.

`horizon_days` representa observações da frequência diária suportada, não dias
corridos. Calendários alternativos ficam adiados.

### Método da série

O motor preserva o `ReturnMethod` recebido. Resultado simples permanece em retorno
simples; resultado logarítmico permanece em log-retorno. Não há conversão silenciosa.

### Unidade

A Fase 7 entrega somente `relative_return`. VaR monetário é adiado porque multiplicar
pela carteira exige decidir valor líquido ou bruto, data de valoração, moeda e política
de câmbio. Nenhuma dessas bases será presumida.

### Resultado

O resultado inclui configuração, chave, frequência, método de retorno, cenários de
perda, rank, quantil bruto, VaR não negativo, data de referência, convenção de sinal e
unidade. As datas de início e fim da amostra são derivadas dos cenários preservados.

## Consequências positivas

- exemplos pequenos são reconciliáveis por ordenação manual;
- o resultado é determinístico e auditável;
- horizonte de vários dias respeita a matemática do método de retorno;
- cauda sem resolução mínima produz falha estruturada;
- ganho no quantil não é apresentado como perda;
- nenhuma dependência externa é adicionada;
- a amostra preservada poderá apoiar o Expected Shortfall da Fase 8.

## Consequências negativas e custos

- nearest-rank muda em degraus e não interpola;
- janelas de 95% e 99% exigem ao menos 20 e 100 cenários;
- blocos sobrepostos são dependentes entre si;
- log-VaR não é diretamente um percentual simples;
- o piso em zero exige consultar `quantile_loss` para distinguir ganho de zero;
- não há valor monetário nesta fase.

## Alternativas consideradas

### Interpolação linear

Adiada. É comum em bibliotecas numéricas, mas introduz um valor não observado e exige
escolher entre várias definições incompatíveis de percentil.

### Rank `ceil((w + 1) * c)`

Rejeitado nesta fase porque pode produzir rank fora da amostra e demandar regras
adicionais de truncamento.

### Escala pela raiz do horizonte

Rejeitada para VaR histórico porque pressupõe propriedades distribucionais e não
reproduz os retornos históricos agregados.

### Blocos não sobrepostos

Rejeitados porque descartariam a maior parte das datas possíveis e fariam o resultado
depender arbitrariamente do ponto inicial do particionamento.

### Valor absoluto do quantil negativo

Rejeitado porque converteria um ganho histórico em perda positiva. O piso em zero
preserva a interpretação econômica.

### VaR monetário por valor líquido ou bruto

Adiado. Escolher uma base automaticamente seria especialmente enganoso para carteiras
long/short, neutras ou multimoeda.

## Regras verificáveis

- confiança está no intervalo aberto (0, 1);
- janela e horizonte são inteiros positivos;
- janela respeita a resolução mínima da cauda;
- a série fornece ao menos `window + horizon_days - 1` retornos;
- perdas equivalem ao oposto dos retornos de horizonte;
- rank usa nearest-rank sem interpolação;
- VaR é finito, não negativo e reconcilia com o quantil;
- a amostra contém exatamente a janela mais recente;
- resultado registra datas, método, unidade e convenção;
- o core não importa arquivo, provider, cache, Qt ou Expected Shortfall.

## Critério de reconsideração

Esta decisão deve ser revista quando forem adicionados Expected Shortfall, outras
definições de quantil, pesos temporais, frequências além de diária, calendários,
conversão monetária ou backtesting. Novas opções devem permanecer explícitas e não
alterar silenciosamente resultados existentes.

## Relações

- [Value at Risk histórico](../concepts/historical-var.md)
- [ADR-005 — Expected Shortfall histórico](ADR-005-historical-expected-shortfall-conventions.md)
- [Analytics básicos](../concepts/basic-analytics.md)
- [Visão geral da arquitetura](../architecture/overview.md)
- [Glossário](../glossary.md)
