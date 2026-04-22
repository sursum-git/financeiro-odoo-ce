# FASE 4 - custom_treasury_bank

## Objetivo da fase
Adicionar o controle bancário, com cadastro de bancos, contas bancárias, modalidades de conta e importação básica de extrato.

## Nome do addon
`custom_treasury_bank`

## Dependências
- `custom_treasury`

## Estrutura esperada

custom_treasury_bank/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - treasury_bank.py
  - treasury_bank_account.py
  - treasury_bank_account_modality.py
  - treasury_bank_statement_import.py
  - treasury_bank_statement_line.py
- views/
  - menu.xml
  - treasury_bank_views.xml
  - treasury_bank_account_views.xml
  - treasury_bank_account_modality_views.xml
  - treasury_bank_statement_import_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_treasury_bank.py

## Modelos a implementar

### 1. treasury.bank
#### Campos
- `name`
- `code`
- `active`

### 2. treasury.bank.account
#### Campos
- `name`
- `bank_id`
- `treasury_account_id`
- `agency`
- `account_number`
- `account_digit`
- `company_id`
- `active`

#### Regra
Pode se relacionar com uma conta de tesouraria.

### 3. treasury.bank.account.modality
#### Campos
- `bank_account_id`
- `modality_id`
- `code`
- `active`

### 4. treasury.bank.statement.import
#### Campos
- `name`
- `file_name`
- `file_data`
- `company_id`
- `bank_account_id`
- `state`
- `notes`

### 5. treasury.bank.statement.line
#### Campos
- `import_id`
- `date`
- `description`
- `document_number`
- `amount`
- `type`
- `is_reconciled`
- `movement_id`

## Regras de negócio

### Regra 1
Extrato importado não altera saldo sozinho.

### Regra 2
Linha importada só vira efeito financeiro via conciliação ou processo específico.

### Regra 3
Conta bancária pode ter múltiplas modalidades.

### Regra 4
Tarifas e despesas bancárias devem poder gerar movimentos rastreáveis.

## Funcionalidades mínimas
- CRUD de banco
- CRUD de conta bancária
- CRUD de conta x modalidade
- Importação simples de extrato em formato controlado pelo projeto

## Testes obrigatórios

### Teste 1
Criar banco.

### Teste 2
Criar conta bancária.

### Teste 3
Associar modalidade à conta bancária.

### Teste 4
Criar importação de extrato.

### Teste 5
Criar linhas importadas sem alterar saldo automaticamente.

## Critérios de aceite
- Módulo instala
- Cadastros funcionam
- Extrato é armazenado
- Testes passam
