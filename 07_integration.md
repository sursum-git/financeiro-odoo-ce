# FASE 7 - custom_financial_integration

## Objetivo da fase
Centralizar a integração entre tesouraria, contas a receber e contas a pagar, impedindo que cada módulo mexa em saldo ou crie movimentos da sua própria forma.

## Nome do addon
`custom_financial_integration`

## Dependências
- `custom_treasury`
- `custom_account_receivable`
- `custom_account_payable`

## Estrutura esperada

custom_financial_integration/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - financial_integration_event.py
  - financial_integration_log.py
- services/
  - __init__.py
  - financial_integration_service.py
- views/
  - menu.xml
  - financial_integration_event_views.xml
  - financial_integration_log_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_financial_integration.py

## Modelos a implementar

### 1. financial.integration.event
#### Campos
- `name`
- `company_id`
- `event_type`
- `source_module`
- `source_model`
- `source_record_id`
- `state`
- `notes`

#### event_type sugeridos
- `receivable_settlement`
- `payable_payment`
- `reverse_receivable`
- `reverse_payable`
- `transfer_portador`

### 2. financial.integration.log
#### Campos
- `event_id`
- `level`
- `message`
- `created_at`

## Serviço principal

### financial_integration_service.py
Implementar serviço central com métodos como:

- `create_treasury_entry_from_receivable_settlement(settlement)`
- `create_treasury_exit_from_payable_payment(payment)`
- `reverse_treasury_movement_from_source(source_model, source_record_id)`
- `log_event(event, level, message)`

## Regras de negócio obrigatórias

### Regra 1
Somente este módulo pode criar movimentos automáticos originados de receber e pagar.

### Regra 2
Receber e pagar devem chamar a camada de integração e nunca criar movimento diretamente.

### Regra 3
Toda integração deve registrar origem e resultado.

### Regra 4
Se falhar a criação do movimento de tesouraria, a liquidação/pagamento deve falhar de forma transacional, salvo regra futura explícita de fila.

### Regra 5
Deve haver vínculo rastreável entre:
- liquidação/pagamento de origem
- evento de integração
- movimento de tesouraria gerado

## Implementação recomendada
Adicionar campos de rastreamento nos movimentos criados:
- `origin_module`
- `origin_model`
- `origin_record_id`

## Testes obrigatórios

### Teste 1
Liquidação do receber gera movimento de entrada.

### Teste 2
Pagamento do pagar gera movimento de saída.

### Teste 3
Falha na integração impede conclusão da operação de origem.

### Teste 4
Evento e log são criados.

### Teste 5
Rastreio entre origem e movimento fica correto.

## Critérios de aceite
- Integração funciona
- Receber e pagar não geram movimento por conta própria
- Logs existem
- Testes passam
