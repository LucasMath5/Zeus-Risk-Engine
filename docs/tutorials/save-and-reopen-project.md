# Salvar e reabrir um projeto

## Abrir o exemplo pronto

Inicie a aplicação:

```powershell
.venv\Scripts\zeus-risk-gui.exe
```

Use **Arquivo → Abrir projeto** e selecione:

```text
assets/samples/historical-risk-demo.zeus.json
```

A aplicação restaura a carteira, os preços locais, confiança de 50%, horizonte de um
dia, janela de dois cenários e método de retorno simples. Clique em **Executar análise**
para reproduzir o VaR e o Expected Shortfall do tutorial anterior.

## Criar e salvar um projeto

1. Importe uma carteira CSV ou XLSX válida.
2. Selecione o CSV de preços.
3. Configure confiança, horizonte e janela.
4. Use **Arquivo → Salvar projeto como**.
5. Escolha um nome terminado em `.zeus.json`.

Depois do salvamento, o título deixa de mostrar `*`. Qualquer alteração nos arquivos
selecionados ou nos três parâmetros volta a marcar o projeto como não salvo. **Salvar
projeto** (`Ctrl+S`) atualiza o destino atual; **Salvar projeto como** escolhe outro.

## Tornar o projeto portátil

Salve o JSON em uma pasta que também contenha a carteira e os preços, ou em uma pasta
acima deles. Referências contidas nessa árvore são gravadas de modo relativo. Copie a
árvore completa para outro local; copiar apenas o JSON não copia os dados.

## Falhas comuns

- `PROJECT_PORTFOLIO_FILE_NOT_FOUND`: a carteira foi movida ou removida;
- `PROJECT_MARKET_DATA_FILE_NOT_FOUND`: o CSV de preços não está mais no caminho;
- `UNSUPPORTED_PROJECT_SCHEMA_VERSION`: o arquivo pertence a um schema não suportado;
- `UNKNOWN_PROJECT_FIELD`: o JSON foi editado com um campo desconhecido;
- `PROJECT_PORTFOLIO_INVALID`: a carteira existe, mas seu conteúdo deixou de ser válido.

Uma falha ao abrir não substitui o projeto que já estava na janela. Corrija a referência
ou o conteúdo no arquivo de origem e tente novamente.
