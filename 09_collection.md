# FASE 9 - custom_account_receivable_collection

## Objetivo da fase
Adicionar a camada de cobrança operacional do contas a receber, incluindo roteiros, cobradores, recebimento em campo e prestação de contas.

## Nome do addon
`custom_account_receivable_collection`

## Dependências
- `custom_account_receivable`
- `custom_treasury_cash`
- `custom_financial_integration`

## Estrutura esperada

custom_account_receivable_collection/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - receivable_collection_agent.py
  - receivable_collection_route.py
  - receivable_collection_assignment.py
  - receivable_collection_accountability.py
- services/
  - __init__.py
  - receivable_collection_service.py
- views/
  - menu.xml
  - receivable_collection_agent_views.xml
  - receivable_collection_route_views.xml
  - receivable_collection_assignment_views.xml
  - receivable_collection_accountability_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_receivable_collection.py

## Modelos a implementar

### 1. receivable.collection.agent
#### Campos
- `name`
- `partner_id`
- `user_id`
- `portador_id`
- `company_id`
- `active`

#### Regra
Cada cobrador pode estar vinculado a um portador do tipo cobrador.

### 2. receivable.collection.route
#### Campos
- `name`
- `company_id`
- `date`
- `state`
- `notes`

### 3. receivable.collection.assignment
#### Campos
- `route_id`
- `agent_id`
- `partner_id`
- `title_id`
- `installment_id`
- `state`
- `notes`

### 4. receivable.collection.accountability
#### Campos
- `name`
- `agent_id`
- `date`
- `amount`
- `target_account_id`
- `target_cash_box_id`
- `state`
- `notes`

## Regras de negócio

### Regra 1
Recebimento em campo deve poder entrar em portador do cobrador.

### Regra 2
Prestação de contas do cobrador deve transferir saldo para conta/caixa de destino.

### Regra 3
Não permitir prestação de contas sem rastreabilidade do valor recebido.

### Regra 4
Atribuição de cobrança deve manter histórico.

## Serviço obrigatório
Métodos sugeridos:
- `assign_titles_to_agent(...)`
- `register_field_collection(...)`
- `create_agent_accountability(...)`

## Testes obrigatórios

### Teste 1
Criar cobrador com portador.

### Teste 2
Atribuir título a cobrador.

### Teste 3
Registrar recebimento em campo.

### Teste 4
Executar prestação de contas.

### Teste 5
Transferir saldo do portador do cobrador.

## Critérios de aceite
- Fluxo básico de cobrança funciona
- Prestação de contas funciona
- Testes passam
