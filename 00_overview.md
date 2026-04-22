# OVERVIEW - ARQUITETURA FINANCEIRA PARA ODOO CE

## Objetivo
Construir um conjunto modular de addons financeiros para Odoo CE, divididos por responsabilidade, com baixo acoplamento, alta rastreabilidade e possibilidade de evolução futura.

## Princípios obrigatórios

- Separação entre obrigação financeira e movimentação financeira
- Saldo é consequência de movimentos, nunca fonte primária
- Estorno ao invés de exclusão física
- Multiempresa desde a base
- Trilhas de auditoria em todas as operações críticas
- Integração centralizada entre módulos
- Código desacoplado, com serviços reutilizáveis
- Testes automatizados em cada fase
- Views simples primeiro, refinamento depois
- Evitar acoplamento prematuro com contabilidade nativa, exceto onde for estritamente necessário

## Módulos propostos

1. `custom_financial_base`
2. `custom_treasury`
3. `custom_treasury_cash`
4. `custom_treasury_bank`
5. `custom_account_receivable`
6. `custom_account_payable`
7. `custom_financial_integration`
8. `custom_treasury_reconciliation`
9. `custom_account_receivable_collection`
10. `custom_financial_reports`

## Ordem obrigatória de execução

1. Base
2. Tesouraria núcleo
3. Caixa
4. Banco
5. Contas a receber
6. Contas a pagar
7. Integração
8. Conciliação
9. Cobrança
10. Relatórios

## Estrutura padrão de cada addon

Cada módulo deve conter, no mínimo:

- `__manifest__.py`
- `__init__.py`
- `models/`
- `views/`
- `security/`
- `data/`
- `tests/`

Quando necessário:

- `wizard/`
- `report/`
- `services/`

## Regras globais de negócio

### Regra 1
Nenhum módulo deve alterar saldo diretamente em campo persistido como fonte de verdade.

### Regra 2
Toda entrada, saída, ajuste, estorno ou transferência deve gerar movimento rastreável.

### Regra 3
Receber e pagar não podem criar movimento de tesouraria diretamente. Devem chamar a camada de integração.

### Regra 4
Movimento conciliado não pode ser alterado livremente.

### Regra 5
Portador pode existir sem conta e sem modalidade.

### Regra 6
Conta pode ter várias modalidades.

### Regra 7
Modalidade é contextual e não se aplica a todo portador.

### Regra 8
Toda integração deve registrar origem:
- módulo
- modelo
- id do registro
- usuário
- data/hora

### Regra 9
Toda fase deve incluir testes automatizados.

### Regra 10
Toda fase deve ser instalada e validada no Odoo CE antes da próxima.

## Como o Codex deve trabalhar

Para cada fase:

1. Ler este overview e o arquivo da fase correspondente
2. Criar ou atualizar o addon correspondente
3. Implementar models
4. Implementar services
5. Implementar views
6. Implementar segurança
7. Implementar dados iniciais, se houver
8. Implementar testes
9. Instalar o módulo em ambiente Odoo
10. Executar os testes
11. Corrigir erros
12. Só depois seguir para a próxima fase

## Critérios gerais de aceite

- Módulo instala sem erro
- Sem dependências quebradas
- Menus e telas básicas funcionam
- Regras centrais respeitadas
- Testes automatizados passam
- Código organizado para evolução futura

## Convenções recomendadas

### Nomenclatura de models
Usar nomes técnicos claros e estáveis, por exemplo:
- `financial.portador`
- `treasury.movement`
- `receivable.title`
- `payable.title`

### Segurança
Criar grupos específicos por papel:
- operador de caixa
- tesouraria
- financeiro receber
- financeiro pagar
- supervisor financeiro
- auditor

### Logs
Toda falha em integração deve ser registrada de forma legível ao usuário e rastreável tecnicamente.

## Observação final
O objetivo não é construir um monólito. O objetivo é criar um conjunto de addons coesos, cada um com responsabilidade bem definida e integração disciplinada.
