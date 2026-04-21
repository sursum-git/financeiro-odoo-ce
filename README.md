# Financeiro Odoo CE

Suite financeira modular para Odoo CE, implementada em 10 fases, cobrindo base cadastral, tesouraria, caixa, bancos, contas a receber, contas a pagar, integração financeira, conciliação, cobrança e relatórios.

## Objetivo

Este projeto organiza o domínio financeiro em addons independentes, mas integrados, para manter:
- rastreabilidade de ponta a ponta
- separação entre obrigação financeira e movimentação financeira
- saldo sempre derivado de movimentos postados
- conciliação e prestação de contas sem perda de histórico

## Addons Entregues

- `custom_financial_base`: cadastros base, portadores, formas de pagamento, modalidades, históricos, motivos e parâmetros
- `custom_treasury`: núcleo da tesouraria, contas financeiras, movimentos, transferências, saldo e estornos
- `custom_treasury_cash`: operação de caixa, sessões, suprimento, sangria e prestação de contas
- `custom_treasury_bank`: bancos, contas bancárias e importação de extrato
- `custom_account_receivable`: títulos a receber, parcelas, liquidações, juros e renegociação
- `custom_account_payable`: títulos a pagar, parcelas, programação e pagamentos
- `custom_financial_integration`: integração central entre receber, pagar e tesouraria
- `custom_treasury_reconciliation`: conciliação entre extrato e tesouraria, incluindo ajustes
- `custom_account_receivable_collection`: cobrança operacional, roteiros, cobradores, recebimento em campo e prestação de contas
- `custom_financial_reports`: consultas e relatórios analíticos somente leitura

## Princípios de Arquitetura

- Contas a receber e a pagar não devem movimentar tesouraria diretamente.
- Toda entrada ou saída financeira relevante passa por `custom_financial_integration` ou por serviços próprios de tesouraria/caixa.
- Extrato bancário importado não altera saldo automaticamente.
- Estorno preserva histórico e não substitui exclusão física.
- Relatórios não alteram dados transacionais.

## Estrutura

Cada addon segue o padrão:

- `models/`
- `services/`
- `views/`
- `security/`
- `tests/`

## Requisitos

- Odoo 19 CE
- PostgreSQL acessível ao Odoo
- addons path contendo a raiz do projeto

## Instalacao

Exemplo de carga dos módulos:

```bash
odoo -c /proj_edi_odoo/deploy/odoo-test.conf \
  --db_host db --db_port 5432 --db_user odoo --db_password odoo \
  --database odoo_financial \
  --init custom_financial_base,custom_treasury,custom_treasury_cash,custom_treasury_bank,custom_account_receivable,custom_account_payable,custom_financial_integration,custom_treasury_reconciliation,custom_account_receivable_collection,custom_financial_reports
```

## Validacao

As fases foram validadas individualmente e também em conjunto.

Validacao integrada dos módulos do projeto:

```bash
odoo -c /proj_edi_odoo/deploy/odoo-test.conf \
  --db_host db --db_port 5432 --db_user odoo --db_password odoo \
  --database odoo_test_financial_suite_integrated_scoped \
  --init custom_financial_base,custom_treasury,custom_treasury_cash,custom_treasury_bank,custom_account_receivable,custom_account_payable,custom_financial_integration,custom_treasury_reconciliation,custom_account_receivable_collection,custom_financial_reports \
  --test-enable \
  --test-tags /custom_financial_base,/custom_treasury,/custom_treasury_cash,/custom_treasury_bank,/custom_account_receivable,/custom_account_payable,/custom_financial_integration,/custom_treasury_reconciliation,/custom_account_receivable_collection,/custom_financial_reports \
  --http-port 8101 \
  --stop-after-init
```

Resultado da validacao integrada:

- `0 failed, 0 error(s) of 53 tests`

## Homologacao

O checklist funcional esta em:

- [FINANCIAL_HOMOLOGATION_CHECKLIST.md](./FINANCIAL_HOMOLOGATION_CHECKLIST.md)

## Status

Projeto implementado no escopo funcional definido pelo pacote de especificação:

- 10 fases concluídas
- testes focados por módulo
- validacao integrada dos módulos financeiros
- checklist de homologação incluído

## Observacoes

- Uma execução de testes sem filtro pode incluir testes nativos do próprio Odoo, inclusive testes do módulo `base` que dependem do empacotamento local do `odoo-bin`. Para validar o projeto, use a suíte filtrada dos módulos financeiros.
