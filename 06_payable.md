# FASE 6 - custom_account_payable

## Objetivo da fase
Criar o módulo de contas a pagar, com títulos, parcelas, programação de pagamento e liquidação, mantendo a separação em relação à tesouraria.

## Nome do addon
`custom_account_payable`

## Dependências
- `custom_financial_base`
- integrar com `purchase` futuramente se necessário

## Estrutura esperada

custom_account_payable/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - payable_title.py
  - payable_installment.py
  - payable_payment.py
  - payable_payment_line.py
  - payable_schedule.py
- services/
  - __init__.py
  - payable_service.py
- views/
  - menu.xml
  - payable_title_views.xml
  - payable_installment_views.xml
  - payable_payment_views.xml
  - payable_schedule_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_payable.py

## Modelos a implementar

### 1. payable.title
#### Campos
- `name`
- `partner_id`
- `company_id`
- `issue_date`
- `origin_reference`
- `amount_total`
- `amount_open`
- `state`
- `notes`

### 2. payable.installment
#### Campos
- `title_id`
- `sequence`
- `due_date`
- `amount`
- `amount_open`
- `state`

### 3. payable.payment
Liquidação do pagar.

#### Campos
- `name`
- `date`
- `partner_id`
- `company_id`
- `payment_method_id`
- `source_account_id`
- `source_portador_id`
- `state`
- `notes`

### 4. payable.payment.line
#### Campos
- `payment_id`
- `installment_id`
- `principal_amount`
- `interest_amount`
- `fine_amount`
- `discount_amount`
- `total_amount`

### 5. payable.schedule
Programação de pagamento.

#### Campos
- `name`
- `payment_date`
- `company_id`
- `partner_id`
- `state`
- `notes`

## Regras de negócio

### Regra 1
Título a pagar não movimenta tesouraria sozinho.

### Regra 2
Pagamento parcial deve manter saldo residual correto.

### Regra 3
Não permitir pagamento acima do saldo em aberto.

### Regra 4
Programação de pagamento não equivale a liquidação.

### Regra 5
Liquidação deve atualizar parcela e título.

## Serviços obrigatórios
Métodos sugeridos:
- `open_title(...)`
- `generate_installments(...)`
- `schedule_payment(...)`
- `create_payment(...)`
- `apply_payment(...)`

## Testes obrigatórios

### Teste 1
Criar título a pagar.

### Teste 2
Criar parcelas.

### Teste 3
Programar pagamento.

### Teste 4
Executar pagamento parcial.

### Teste 5
Bloquear pagamento acima do saldo.

## Critérios de aceite
- Módulo instala
- Fluxo básico de pagar funciona
- Programação funciona
- Testes passam
