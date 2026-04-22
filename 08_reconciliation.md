# FASE 8 - custom_treasury_reconciliation

## Objetivo da fase
Criar o módulo de conciliação bancária entre extratos importados e movimentos de tesouraria.

## Nome do addon
`custom_treasury_reconciliation`

## Dependências
- `custom_treasury_bank`
- `custom_treasury`

## Estrutura esperada

custom_treasury_reconciliation/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - treasury_reconciliation.py
  - treasury_reconciliation_line.py
- services/
  - __init__.py
  - treasury_reconciliation_service.py
- views/
  - menu.xml
  - treasury_reconciliation_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_treasury_reconciliation.py

## Modelos a implementar

### 1. treasury.reconciliation
#### Campos
- `name`
- `company_id`
- `bank_account_id`
- `date_start`
- `date_end`
- `state`
- `notes`

### 2. treasury.reconciliation.line
#### Campos
- `reconciliation_id`
- `statement_line_id`
- `movement_id`
- `status`
- `difference_amount`
- `notes`

#### status sugeridos
- `pending`
- `matched`
- `divergent`
- `adjusted`

## Regras de negócio

### Regra 1
Linha de extrato não pode ser conciliada duas vezes.

### Regra 2
Movimento conciliado não pode ser alterado livremente.

### Regra 3
Ajuste de conciliação deve gerar movimento próprio.

### Regra 4
Conciliação deve guardar usuário, data e vínculo entre extrato e movimento.

## Serviço obrigatório
Métodos sugeridos:
- `suggest_matches(reconciliation)`
- `match_line(statement_line, movement)`
- `create_adjustment(...)`
- `finalize_reconciliation(reconciliation)`

## Testes obrigatórios

### Teste 1
Criar conciliação.

### Teste 2
Vincular linha de extrato a movimento.

### Teste 3
Impedir dupla conciliação.

### Teste 4
Criar ajuste de conciliação.

### Teste 5
Marcar movimento conciliado.

## Critérios de aceite
- Conciliação básica funciona
- Regras de bloqueio funcionam
- Ajuste funciona
- Testes passam
