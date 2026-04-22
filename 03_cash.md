# FASE 3 - custom_treasury_cash

## Objetivo da fase
Adicionar o controle operacional de caixa físico, incluindo abertura, fechamento, sangria, suprimento e prestação de contas.

## Nome do addon
`custom_treasury_cash`

## Dependências
- `custom_treasury`

## Estrutura esperada

custom_treasury_cash/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - treasury_cash_box.py
  - treasury_cash_session.py
  - treasury_cash_session_line.py
  - treasury_cash_accountability.py
- services/
  - __init__.py
  - treasury_cash_service.py
- views/
  - menu.xml
  - treasury_cash_box_views.xml
  - treasury_cash_session_views.xml
  - treasury_cash_accountability_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_treasury_cash.py

## Conceitos da fase

### Caixa
É o ponto operacional de movimentação física.

### Sessão de caixa
Define o período em que um caixa está aberto sob responsabilidade de um operador.

### Prestação de contas
Transfere responsabilidade de saldo do caixa ou portador para conta/caixa de destino.

## Modelos a implementar

### 1. treasury.cash.box
#### Campos
- `name`
- `code`
- `company_id`
- `portador_id` (opcional, mas recomendado)
- `active`

### 2. treasury.cash.session
#### Campos
- `name`
- `cash_box_id`
- `company_id`
- `user_id`
- `opened_at`
- `opening_amount`
- `closed_at`
- `closing_amount_informed`
- `closing_amount_computed`
- `difference_amount`
- `difference_reason`
- `state`

#### Estados sugeridos
- `draft`
- `open`
- `closed`
- `cancelled`

#### Regras
- Não permitir duas sessões abertas para o mesmo caixa
- Não permitir movimentar caixa sem sessão aberta
- Fechamento deve calcular diferença
- Diferença exige justificativa conforme parâmetro

### 3. treasury.cash.session.line
#### Campos
- `session_id`
- `movement_id`

Serve para vincular movimentos à sessão, quando necessário.

### 4. treasury.cash.accountability
Prestação de contas do caixa ou portador.

#### Campos
- `name`
- `date`
- `company_id`
- `source_portador_id`
- `target_account_id`
- `target_portador_id`
- `amount`
- `state`
- `notes`

#### Regras
- Ao confirmar, gerar movimentos de saída e entrada conforme destino
- Deve reduzir saldo operacional do portador de origem

## Serviços obrigatórios

### treasury_cash_service.py
Métodos sugeridos:
- `open_session(cash_box, user, opening_amount)`
- `close_session(session, informed_amount, reason=None)`
- `register_supply(session, amount, history=None)`
- `register_withdrawal(session, amount, history=None)`
- `create_accountability(...)`

## Regras de negócio centrais

### Regra 1
Caixa depende de sessão aberta.

### Regra 2
Suprimento e sangria devem gerar movimentos financeiros.

### Regra 3
Fechamento não pode apagar histórico.

### Regra 4
Diferença deve ficar registrada e auditável.

## Views
Criar:
- cadastro de caixa
- abertura/fechamento de sessão
- consulta das sessões
- prestação de contas

## Testes obrigatórios

### Teste 1
Criar caixa.

### Teste 2
Abrir sessão.

### Teste 3
Bloquear segunda sessão aberta para o mesmo caixa.

### Teste 4
Registrar suprimento.

### Teste 5
Registrar sangria.

### Teste 6
Fechar sessão e calcular diferença.

### Teste 7
Criar prestação de contas.

## Critérios de aceite
- Sessão funciona
- Regras de bloqueio funcionam
- Prestação de contas gera reflexos
- Testes passam
