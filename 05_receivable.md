# FASE 5 - custom_account_receivable

## Objetivo da fase
Criar o módulo de contas a receber, responsável pelos títulos, parcelas, liquidação, juros, multa, desconto e renegociação, sem assumir o papel da tesouraria.

## Nome do addon
`custom_account_receivable`

## Dependências
- `custom_financial_base`
- `base`
- `mail` opcional
- integrar com `sale` futuramente, mas não obrigatório agora

## Estrutura esperada

custom_account_receivable/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - receivable_title.py
  - receivable_installment.py
  - receivable_settlement.py
  - receivable_settlement_line.py
  - receivable_interest_rule.py
  - receivable_renegotiation.py
- services/
  - __init__.py
  - receivable_service.py
- views/
  - menu.xml
  - receivable_title_views.xml
  - receivable_installment_views.xml
  - receivable_settlement_views.xml
  - receivable_interest_rule_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_receivable.py

## Modelos a implementar

### 1. receivable.title
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

#### Estados sugeridos
- `draft`
- `open`
- `partial`
- `paid`
- `cancelled`
- `renegotiated`

### 2. receivable.installment
#### Campos
- `title_id`
- `sequence`
- `due_date`
- `amount`
- `amount_open`
- `state`

#### Regra
Um título pode ter várias parcelas.

### 3. receivable.settlement
Liquidação do receber.

#### Campos
- `name`
- `date`
- `partner_id`
- `company_id`
- `payment_method_id`
- `portador_id`
- `target_account_id`
- `state`
- `notes`

#### Regra
Não cria tesouraria diretamente nesta fase. Apenas prepara a baixa.

### 4. receivable.settlement.line
#### Campos
- `settlement_id`
- `installment_id`
- `principal_amount`
- `interest_amount`
- `fine_amount`
- `discount_amount`
- `total_amount`

### 5. receivable.interest.rule
#### Campos
- `name`
- `interest_type`
- `interest_value`
- `fine_type`
- `fine_value`
- `discount_type`
- `discount_value`
- `company_id`
- `active`

### 6. receivable.renegotiation
#### Campos
- `name`
- `partner_id`
- `source_title_ids`
- `new_title_id`
- `date`
- `state`

## Regras de negócio

### Regra 1
Título a receber não movimenta tesouraria sozinho.

### Regra 2
Liquidação é evento financeiro do módulo receber, mas o reflexo em tesouraria será responsabilidade da integração na fase posterior.

### Regra 3
Não permitir liquidação acima do saldo aberto.

### Regra 4
Permitir baixa parcial.

### Regra 5
Liquidação deve recalcular saldo da parcela e do título.

### Regra 6
Renegociação deve preservar vínculo com os títulos de origem.

## Serviços obrigatórios
Criar serviço com métodos como:
- `open_title(...)`
- `generate_installments(...)`
- `create_settlement(...)`
- `apply_settlement(...)`
- `renegotiate_titles(...)`

## Views
Criar:
- título
- parcelas
- liquidação
- regras de juros

## Testes obrigatórios

### Teste 1
Criar título a receber.

### Teste 2
Criar parcelas.

### Teste 3
Criar liquidação parcial.

### Teste 4
Atualizar saldo em aberto.

### Teste 5
Bloquear liquidação acima do saldo.

### Teste 6
Criar renegociação.

## Critérios de aceite
- Módulo instala
- Título e parcelas funcionam
- Liquidação parcial funciona
- Renegociação mínima funciona
- Testes passam
