# FASE 10 - custom_financial_reports

## Objetivo da fase
Concentrar relatórios e consultas gerenciais dos módulos financeiros sem poluir os módulos transacionais.

## Nome do addon
`custom_financial_reports`

## Dependências
- `custom_treasury`
- `custom_treasury_cash`
- `custom_treasury_bank`
- `custom_account_receivable`
- `custom_account_payable`
- `custom_treasury_reconciliation`
- `custom_account_receivable_collection` quando instalado

## Estrutura esperada

custom_financial_reports/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - financial_report_helper.py
- views/
  - menu.xml
  - treasury_report_views.xml
  - receivable_report_views.xml
  - payable_report_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_financial_reports.py

## Relatórios mínimos a entregar

### Tesouraria
- Extrato por conta
- Extrato por portador
- Saldo por conta
- Saldo por portador
- Fluxo de caixa realizado

### Contas a receber
- Posição em aberto por cliente
- Aging de vencidos
- Histórico de liquidações

### Contas a pagar
- Posição em aberto por fornecedor
- Agenda de pagamentos
- Histórico de pagamentos

### Conciliação
- Itens conciliados
- Itens divergentes

### Cobrança
- Prestação de contas por cobrador
- Títulos em rota

## Regras de negócio

### Regra 1
Relatórios são somente leitura.

### Regra 2
Nenhum relatório pode alterar dados transacionais.

### Regra 3
Todos os filtros devem respeitar empresa e permissões.

## Implementação recomendada
Começar com ações e views analíticas simples. Depois evoluir para pivots e gráficos se necessário.

## Testes obrigatórios

### Teste 1
Abrir extrato por conta.

### Teste 2
Abrir posição de receber.

### Teste 3
Abrir posição de pagar.

### Teste 4
Garantir que relatório não altera registros.

## Critérios de aceite
- Relatórios mínimos acessíveis
- Filtros funcionam
- Sem escrita indevida
- Testes passam
