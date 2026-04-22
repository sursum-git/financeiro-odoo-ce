# FASE 2 - custom_treasury

## Objetivo da fase
Criar o núcleo de tesouraria, responsável pela movimentação financeira real, controle de contas financeiras, transferências e base para cálculo de saldo.

## Nome do addon
`custom_treasury`

## Dependências
- `custom_financial_base`

## Estrutura esperada

custom_treasury/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - treasury_account.py
  - treasury_account_modality.py
  - treasury_movement.py
  - treasury_movement_payment_line.py
  - treasury_transfer.py
- services/
  - __init__.py
  - treasury_movement_service.py
- views/
  - menu.xml
  - treasury_account_views.xml
  - treasury_account_modality_views.xml
  - treasury_movement_views.xml
  - treasury_transfer_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_treasury.py

## Conceitos da fase

### Conta financeira
Representa onde o dinheiro fica ou é controlado financeiramente:
- conta bancária
- conta interna
- tesouraria
- caixa central, se fizer sentido na modelagem

### Movimento financeiro
É a fonte de verdade da tesouraria.

### Transferência
É operação composta, que deve gerar pelo menos dois reflexos:
- saída na origem
- entrada no destino

## Modelos a implementar

### 1. treasury.account
#### Campos
- `name`
- `code`
- `type` (Selection)
- `company_id`
- `active`

#### Tipos sugeridos
- `bank`
- `cash_internal`
- `treasury`
- `other`

### 2. treasury.account.modality
Relaciona conta com modalidade financeira.

#### Campos
- `account_id` (Many2one treasury.account)
- `modality_id` (Many2one financial.modality)
- `active`
- `code`

#### Regra
Uma conta pode ter várias modalidades.

### 3. treasury.movement
#### Campos obrigatórios
- `name`
- `date`
- `company_id`
- `type` (Selection)
- `amount`
- `account_id` (Many2one treasury.account, opcional conforme cenário)
- `portador_id` (Many2one financial.portador, opcional)
- `payment_method_id` (Many2one financial.payment.method, opcional)
- `history_id`
- `reason_id`
- `origin_module`
- `origin_model`
- `origin_record_id`
- `state`
- `is_reconciled` (Boolean)
- `reversed_movement_id` (Many2one self)
- `active`

#### Tipos sugeridos
- `entrada`
- `saida`
- `transferencia_entrada`
- `transferencia_saida`
- `ajuste`
- `estorno`
- `tarifa`
- `deposito`
- `saque`

#### Estados sugeridos
- `draft`
- `posted`
- `cancelled`

#### Regras
- Valor deve ser positivo; sentido é dado pelo tipo
- Não permitir exclusão após posted
- Estorno deve criar novo movimento, não alterar histórico
- Movimento conciliado não pode ser editado livremente

### 4. treasury.movement.payment.line
Permite compor um movimento por forma de pagamento, quando necessário.

#### Campos
- `movement_id`
- `payment_method_id`
- `portador_id`
- `amount`
- `details`

### 5. treasury.transfer
#### Campos
- `name`
- `date`
- `company_id`
- `source_account_id`
- `source_portador_id`
- `target_account_id`
- `target_portador_id`
- `amount`
- `state`
- `out_movement_id`
- `in_movement_id`
- `notes`

#### Regras
- Não permitir origem e destino vazios ao mesmo tempo
- Não permitir origem igual ao destino
- Ao confirmar, gerar dois movimentos
- Ao cancelar, exigir estorno dos reflexos

## Serviços obrigatórios

### treasury_movement_service.py
Criar serviço central com métodos como:
- `create_movement(vals)`
- `post_movement(movement)`
- `reverse_movement(movement, reason=None)`
- `compute_balance(account=None, portador=None, company=None)`

## Regras de negócio centrais

### Regra 1
Saldo não é digitado manualmente como fonte primária.

### Regra 2
Saldo é calculado a partir de movimentos posted.

### Regra 3
Toda transferência gera dois movimentos.

### Regra 4
Movimento originado por integração externa deve guardar rastreio de origem.

### Regra 5
Não permitir alteração arbitrária de movimentos posted.

## Views
Criar:
- menus
- tree/form para contas
- tree/form para movimentos
- tree/form para transferências

## Testes obrigatórios

### Teste 1
Criar conta financeira.

### Teste 2
Criar movimento de entrada.

### Teste 3
Criar movimento de saída.

### Teste 4
Criar transferência e validar geração dos dois movimentos.

### Teste 5
Executar estorno e validar vínculo ao movimento original.

### Teste 6
Verificar cálculo de saldo por conta.

## Critérios de aceite
- Módulo instala sem erro
- Transferência funciona
- Estorno funciona
- Cálculo básico de saldo funciona
- Testes passam
