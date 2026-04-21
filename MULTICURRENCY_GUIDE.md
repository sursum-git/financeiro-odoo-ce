# Guia de Multimoeda

## Objetivo

Este documento resume como a suite financeira trata moedas diferentes da moeda-base da empresa.

## Conceitos

- `moeda da transacao`: moeda operacional do documento ou movimento
- `moeda da empresa`: moeda-base da empresa no Odoo
- `valor na moeda da transacao`: valor informado pelo usuario ou pela operacao financeira
- `valor na moeda da empresa`: contravalor convertido na data da transacao

## Onde a moeda e definida

### Portador

Cada `financial.portador` possui moeda propria. Essa moeda orienta:

- movimentos de tesouraria vinculados ao portador
- sessoes de caixa
- prestacoes de contas para portadores
- cobradores e outros portadores operacionais

### Conta bancaria

Cada `treasury.bank.account` possui moeda propria. Essa moeda orienta:

- importacao de extratos
- linhas de extrato
- conciliacao bancaria

### Titulos

Titulos a receber e a pagar possuem moeda propria em:

- `receivable.title`
- `payable.title`

As parcelas herdam a moeda do titulo.

## Regras de operacao

### Tesouraria

`treasury.movement` registra:

- `currency_id`
- `amount`
- `company_currency_id`
- `exchange_rate`
- `amount_company_currency`
- `signed_amount_company_currency`

Se houver portador, a moeda do movimento deve ser a mesma moeda do portador.

### Contas a Receber

`receivable.settlement`:

- herda a moeda das parcelas selecionadas
- nao permite misturar parcelas com moedas diferentes
- calcula bruto, retido e liquido na moeda da transacao
- calcula os mesmos totais na moeda da empresa

### Contas a Pagar

`payable.payment`:

- herda a moeda das parcelas selecionadas
- nao permite misturar parcelas com moedas diferentes
- calcula bruto, retido e liquido na moeda da transacao
- calcula os mesmos totais na moeda da empresa

### Integracao Financeira

Ao integrar receber e pagar com tesouraria:

- o movimento nasce na moeda da transacao
- o valor integrado e o valor liquido da operacao
- o contravalor em moeda da empresa fica no movimento de tesouraria

### Caixa

`treasury.cash.session`:

- usa a moeda do portador do caixa
- soma o fechamento com base nos movimentos da sessao nessa mesma moeda

`treasury.cash.accountability`:

- exige que a moeda bata com o portador de origem
- exige mesma moeda tambem no portador de destino, quando houver

### Banco

`treasury.bank.statement.import` e `treasury.bank.statement.line`:

- usam a moeda da conta bancaria
- guardam valor na moeda do extrato
- guardam valor convertido para a moeda da empresa

### Conciliacao

`treasury.reconciliation`:

- so permite conciliacao entre extrato e movimento na mesma moeda
- cria ajuste na mesma moeda da linha de extrato

## Relatorios

Os relatorios passaram a aceitar filtro por moeda e, em tesouraria, usam:

- valor na moeda da transacao
- valor convertido na moeda da empresa

Isso permite:

- leitura operacional por moeda
- consolidacao gerencial pela moeda-base da empresa

## Homologacao recomendada

Validar pelo menos os cenarios abaixo:

1. portador em moeda estrangeira com movimento direto de tesouraria
2. titulo a receber em moeda estrangeira com liquidacao
3. titulo a pagar em moeda estrangeira com pagamento
4. sessao de caixa em moeda diferente da moeda-base da empresa
5. conta bancaria em moeda estrangeira com importacao de extrato
6. tentativa de conciliacao entre moedas diferentes
7. relatorio filtrado por moeda da transacao

## Limites atuais

Esta etapa nao implementa automaticamente:

- apuracao de ganho/perda cambial
- reavaliacao cambial de saldos em aberto
- contabilizacao automatica de variacao cambial

Esses pontos formam a proxima camada funcional caso o projeto precise avancar para tratamento cambial contabil completo.
