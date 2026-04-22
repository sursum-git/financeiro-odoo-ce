# FASE 1 - custom_financial_base

## Objetivo da fase
Criar a base comum para todos os módulos financeiros, com os cadastros compartilhados, parâmetros globais e estruturas iniciais de segurança.

## Nome do addon
`custom_financial_base`

## Dependências
- `base`
- `mail` pode ser avaliado se for útil para rastreio, mas não é obrigatório nesta primeira fase

## Estrutura esperada

custom_financial_base/
- __init__.py
- __manifest__.py
- models/
  - __init__.py
  - financial_portador.py
  - financial_payment_method.py
  - financial_modality.py
  - financial_history.py
  - financial_movement_reason.py
  - financial_parameter.py
- views/
  - menu.xml
  - financial_portador_views.xml
  - financial_payment_method_views.xml
  - financial_modality_views.xml
  - financial_history_views.xml
  - financial_movement_reason_views.xml
  - financial_parameter_views.xml
- security/
  - ir.model.access.csv
  - security.xml
- tests/
  - __init__.py
  - test_financial_base.py

## Modelos a implementar

### 1. financial.portador
Representa a custódia operacional do valor.

#### Campos obrigatórios
- `name` (Char, required)
- `code` (Char)
- `type` (Selection)
- `controla_saldo` (Boolean, default=True)
- `active` (Boolean, default=True)
- `company_id` (Many2one res.company, opcional ou obrigatório conforme estratégia multiempresa)

#### Valores sugeridos para `type`
- `caixa`
- `banco`
- `cobrador`
- `adquirente`
- `gateway`
- `interno`

#### Regras
- Pode existir sem conta
- Pode existir sem modalidade
- Pode controlar saldo ou não
- Deve permitir desativação sem exclusão

### 2. financial.payment.method
Forma de pagamento.

#### Campos
- `name`
- `code`
- `type` (Selection)
- `liquida_imediato` (Boolean)
- `permite_parcelamento` (Boolean)
- `active`

#### Tipos sugeridos
- `dinheiro`
- `pix`
- `boleto`
- `cartao_credito`
- `cartao_debito`
- `transferencia`
- `cheque`
- `outro`

### 3. financial.modality
Modalidade financeira.

#### Campos
- `name`
- `code`
- `tipo_operacao`
- `active`

#### Exemplos
- carteira
- cobrança simples
- desconto
- caução
- judicial
- cheque

### 4. financial.history
Histórico padrão.

#### Campos
- `name`
- `code`
- `description`
- `active`

### 5. financial.movement.reason
Motivo do movimento.

#### Campos
- `name`
- `code`
- `type`
- `active`

#### Exemplos
- suprimento
- sangria
- ajuste
- tarifa
- estorno
- prestação de contas

### 6. financial.parameter
Parâmetros por empresa.

#### Campos sugeridos
- `company_id`
- `default_portador_id`
- `default_payment_method_id`
- `allow_negative_cash`
- `require_cash_difference_reason`
- `active`

#### Regra
Um registro por empresa, ou lógica equivalente.

## __manifest__.py esperado
O Codex deve criar um manifest com:
- nome legível
- versão
- licença
- depends
- data
- installable=True
- application=False

## Segurança

### Grupos mínimos
- `group_financial_base_user`
- `group_financial_base_manager`

### ACLs
Permissões separadas por modelo.

## Views

Criar:
- tree
- form
- menus

Começar simples. Sem excesso de automação nesta fase.

## Testes obrigatórios

### Teste 1
Criar portador com tipo caixa.

### Teste 2
Criar forma de pagamento PIX.

### Teste 3
Criar modalidade financeira.

### Teste 4
Criar parâmetro financeiro por empresa.

### Teste 5
Garantir que registros essenciais sejam criados e lidos sem erro.

## Critérios de aceite
- Módulo instala no Odoo CE sem erro
- CRUD dos cadastros funciona
- Menus aparecem
- Testes passam
- Nenhum campo crítico ficou sem índice lógico quando necessário

## Observação de implementação
Evitar colocar regra de saldo aqui. Esta fase é apenas fundação.
