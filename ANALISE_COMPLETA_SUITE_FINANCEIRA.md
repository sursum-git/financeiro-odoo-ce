# Análise Completa da Suite Financeira

Data da análise: 2026-04-21

## Escopo analisado

Esta análise cobre os addons financeiros entregues no repositório:

- `custom_financial_base`
- `custom_treasury`
- `custom_treasury_cash`
- `custom_treasury_bank`
- `custom_account_receivable`
- `custom_account_payable`
- `custom_financial_integration`
- `custom_treasury_reconciliation`
- `custom_account_receivable_collection`
- `custom_financial_reports`

Também foram considerados:

- histórico de commits do projeto
- documentação existente (`README.md`, `MULTICURRENCY_GUIDE.md`, `FINANCIAL_HOMOLOGATION_CHECKLIST.md`)
- resultado de validação integrada em banco limpo

## Resumo executivo

O projeto já tem uma base funcional ampla e bem segmentada em módulos, com separação coerente entre cadastro, obrigação financeira, movimentação de tesouraria, conciliação e relatórios. A arquitetura geral é boa e segue um princípio forte: saldo deriva de movimentos e não de digitação manual.

Na primeira rodada desta análise foram encontrados quatro problemas objetivos de implementação e uma lacuna funcional relevante. Em seguida, os quatro problemas de implementação foram corrigidos e revalidados.

Status atual após correções:

1. a regressão funcional em `custom_account_receivable_collection` foi corrigida;
2. a regra de retenção mensal foi corrigida para operar corretamente em cenários multimoeda;
3. o estado `partial` de títulos a receber foi corrigido;
4. a trava de integridade entre soma das parcelas e valor do título foi implementada;
5. adiantamentos de clientes e fornecedores continuam apenas como espécie cadastral, sem fluxo operacional.

## Inventário do que já foi implementado

### 1. Base financeira

Em `custom_financial_base` já existem:

- portadores
- formas de pagamento
- modalidades
- históricos financeiros
- motivos de movimento
- parâmetros por empresa
- espécies de título
- motivos de devolução de cheque
- códigos de retenção por empresa
- associação de múltiplos códigos de retenção por contato e por empresa
- percentual de retenção por linha
- contato favorecido do valor retido
- valor mínimo de retenção por código
- valor mínimo de pagamento por código
- data de vencimento no código de retenção

Observação importante:

- espécies para `normal`, `cheque`, `boleto`, `nota promissória`, `adiantamento de cliente` e `adiantamento de fornecedor` já existem no cadastro base.

### 2. Tesouraria

Em `custom_treasury` já existem:

- contas financeiras
- vínculo conta x modalidade
- movimentos de tesouraria
- post, estorno e cálculo de saldo
- transferências entre contas/portadores
- mútuo entre empresas do mesmo grupo
- rastreabilidade de origem do movimento
- estrutura multimoeda na tesouraria

No modelo atual de tesouraria, o movimento já guarda:

- moeda da transação
- valor na moeda da transação
- moeda da empresa
- taxa de câmbio
- valor convertido na moeda da empresa

### 3. Caixa

Em `custom_treasury_cash` já existem:

- cadastro de caixa
- sessão de caixa
- abertura e fechamento
- suprimento
- sangria
- prestação de contas
- vínculo da sessão com movimentos
- suporte multimoeda seguindo a moeda do portador do caixa

### 4. Bancos

Em `custom_treasury_bank` já existem:

- cadastro de bancos
- cadastro de contas bancárias
- vínculo conta bancária x modalidade
- moeda própria da conta bancária
- importação de extrato
- linhas de extrato com valor na moeda da transação e convertido para moeda da empresa

### 5. Contas a receber

Em `custom_account_receivable` já existem:

- títulos a receber
- parcelas
- liquidação parcial
- juros, multa e desconto
- regra de juros
- renegociação de títulos
- wizard operacional de renegociação
- espécies de título no contas a receber
- recebimento com cheques de terceiros
- substituição do título original por cheques recebidos
- compensação de cheque
- devolução de cheque com motivo
- devolução definitiva gerando novo título normal
- retenção mensal acumulada
- suporte multimoeda em títulos, parcelas e liquidações

### 6. Contas a pagar

Em `custom_account_payable` já existem:

- títulos a pagar
- parcelas
- programação de pagamento
- pagamento parcial
- espécies de título no contas a pagar
- retenção mensal acumulada
- suporte multimoeda em títulos, parcelas e pagamentos

### 7. Integração financeira

Em `custom_financial_integration` já existem:

- evento de integração
- log de integração
- geração centralizada de entrada de tesouraria a partir do receber
- geração centralizada de saída de tesouraria a partir do pagar
- bloqueio transacional quando a integração falha
- preservação da moeda da transação no movimento gerado

### 8. Conciliação

Em `custom_treasury_reconciliation` já existem:

- conciliação entre extrato e tesouraria
- sugestão de match
- conciliação manual
- ajuste de conciliação
- bloqueio de dupla conciliação
- validação de mesma moeda entre extrato e movimento

### 9. Cobrança

Em `custom_account_receivable_collection` já existem:

- cobrador
- roteiro
- atribuição de títulos/recebimentos ao cobrador
- recebimento em campo
- prestação de contas do cobrador
- integração com portador do cobrador

### 10. Relatórios

Em `custom_financial_reports` já existem:

- helper de relatórios somente leitura
- extrato por conta
- posição de contas a receber
- posição de contas a pagar
- leitura analítica por moeda
- agrupamento por moeda em tesouraria

### 11. Padronização de mensagens

Foi padronizado o uso de constantes de classe para mensagens de validação e parte relevante das mensagens operacionais.

### 12. Documentação e homologação

Já existem no repositório:

- `README.md`
- `MULTICURRENCY_GUIDE.md`
- `FINANCIAL_HOMOLOGATION_CHECKLIST.md`
- `FINANCIAL_HOMOLOGATION_CHECKLIST.csv`

## Validação técnica executada nesta análise

Foi rodada uma validação integrada dos módulos financeiros em banco limpo com o comando abaixo:

```bash
odoo -c /proj_financeiro_odoo/deploy/odoo-test.conf \
  --db_host db --db_port 5432 --db_user odoo --db_password odoo \
  --database odoo_test_financial_analysis_20260421 \
  --init custom_financial_base,custom_treasury,custom_treasury_cash,custom_treasury_bank,custom_account_receivable,custom_account_payable,custom_financial_integration,custom_treasury_reconciliation,custom_account_receivable_collection,custom_financial_reports \
  --test-enable \
  --test-tags /custom_financial_base,/custom_treasury,/custom_treasury_cash,/custom_treasury_bank,/custom_account_receivable,/custom_account_payable,/custom_financial_integration,/custom_treasury_reconciliation,/custom_account_receivable_collection,/custom_financial_reports \
  --http-port 8106 \
  --stop-after-init
```

Resultado da primeira execução:

- `0 failed, 2 error(s) of 77 tests`

Os dois erros vieram de `custom_account_receivable_collection`.

Após as correções descritas neste documento, foi rodada uma nova validação integrada:

```bash
odoo -c /proj_financeiro_odoo/deploy/odoo-test.conf \
  --db_host db --db_port 5432 --db_user odoo --db_password odoo \
  --database odoo_test_financial_analysis_fixed2_20260421 \
  --init custom_financial_base,custom_treasury,custom_treasury_cash,custom_treasury_bank,custom_account_receivable,custom_account_payable,custom_financial_integration,custom_treasury_reconciliation,custom_account_receivable_collection,custom_financial_reports \
  --test-enable \
  --test-tags /custom_financial_base,/custom_treasury,/custom_treasury_cash,/custom_treasury_bank,/custom_account_receivable,/custom_account_payable,/custom_financial_integration,/custom_treasury_reconciliation,/custom_account_receivable_collection,/custom_financial_reports \
  --http-port 8109 \
  --stop-after-init
```

Resultado final após correções:

- `0 failed, 0 error(s) of 81 tests`

## Problemas confirmados na análise inicial e status atual

### 1. Regressão atual em prestação de contas da cobrança

Severidade encontrada: alta

Status atual: corrigido

O módulo `custom_account_receivable_collection` hoje está quebrado na validação integrada porque chama `treasury.cash.service.create_accountability()` com a assinatura antiga.

Evidência:

- `custom_account_receivable_collection/services/receivable_collection_service.py:116-124`
- `custom_treasury_cash/services/treasury_cash_service.py:95-105`

Detalhe:

- `create_accountability()` passou a exigir `currency` antes de `company`
- o serviço de cobrança continua chamando sem esse argumento
- o erro reproduzido foi:
  `TypeError: TreasuryCashService.create_accountability() missing 1 required positional argument: 'date'`

Correção aplicada:

- a chamada em `receivable.collection.service` passou a usar argumentos nomeados
- `treasury.cash.service.create_accountability()` passou a aceitar `currency=None` com compatibilidade retroativa e validações explícitas de moeda
- a suíte do módulo de cobrança voltou a passar

### 2. Regra de retenção mensal compara valores em moedas diferentes

Severidade encontrada: alta

Status atual: corrigido

Os limites `minimum_payment_amount` e `minimum_retention_amount` são armazenados na moeda da empresa, mas a regra de retenção compara esses valores com o total mensal na moeda da transação.

Evidência:

- `custom_financial_base/models/financial_withholding_code.py:19-39`
- `custom_account_receivable/services/receivable_service.py:63-70`
- `custom_account_payable/services/payable_service.py:49-56`

Detalhe:

- `financial.withholding.code` usa `currency_id` relacionado a `company_id.currency_id`
- `monthly_gross_total` é somado a partir de `gross_amount_total` da liquidação/pagamento na moeda da transação
- esse total é comparado diretamente com limites definidos na moeda da empresa

Correção aplicada:

- a apuração mensal passou a usar `gross_amount_company_currency`
- o valor já retido passou a usar `amount_company_currency`
- os registros de retenção passaram a guardar tanto valores na moeda da transação quanto valores na moeda da empresa
- foram acrescentados testes cruzando retenção com multimoeda

### 3. Estado do título a receber fica errado em liquidação parcial

Severidade encontrada: média

Status atual: corrigido

O cálculo de estado em `receivable.title` não trata corretamente parcelas em estado `partial`.

Evidência:

- `custom_account_receivable/models/receivable_title.py:193-198`
- comparação correta em `custom_account_payable/models/payable_title.py:70-75`

Detalhe:

- no receber, a regra que define `partial` só considera o caso em que existam parcelas `open` e `paid`
- se a parcela estiver efetivamente `partial`, o título cai no ramo seguinte e fica `open`

Correção aplicada:

- `receivable.title` agora trata explicitamente parcelas em estado `partial`
- foi acrescentado teste cobrindo o estado do título após liquidação parcial

### 4. Falta trava de integridade entre valor do título e soma das parcelas

Severidade encontrada: média

Status atual: corrigido

Hoje é possível criar parcelas cuja soma não bata com `amount_total` do título.

Evidência:

- `custom_account_receivable/services/receivable_service.py:95-106`
- `custom_account_payable/services/payable_service.py:81-93`
- `custom_account_receivable/models/receivable_title.py:177-181`
- `custom_account_payable/models/payable_title.py:62-64`

Detalhe:

- os serviços geram parcelas sem validar total
- `amount_open` passa a derivar da soma das parcelas quando elas existem
- isso permite divergência silenciosa entre valor nominal do título e valor operacional parcelado

Correção aplicada:

- `receivable.service.generate_installments()` e `payable.service.generate_installments()` agora validam que a soma das parcelas seja igual ao valor total do título
- foram acrescentados testes de bloqueio para títulos com soma divergente

### 5. Adiantamentos existem só como cadastro base, não como fluxo operacional

Severidade: média

Status atual: pendente

O projeto já criou espécies para adiantamento de cliente e fornecedor, mas não há tratamento operacional correspondente nos módulos de receber e pagar.

Evidência:

- `custom_financial_base/models/financial_title_species.py:15-24`
- `custom_financial_base/data/financial_title_species_data.xml:23-31`

Resultado da busca no repositório:

- as ocorrências de `customer_advance` e `supplier_advance` aparecem apenas no cadastro base e nos dados iniciais
- não há serviço, wizard, regra de liquidação/compensação nem tela operacional específica para adiantamentos

Impacto:

- o cadastro existe, mas a funcionalidade importante levantada como requisito de negócio ainda não foi implementada

## Fragilidades arquiteturais

### 1. Semântica ambígua de `compute_balance()` em cenário multimoeda

Severidade: média

Hoje `compute_balance()` muda de significado conforme a quantidade de moedas encontrada.

Evidência:

- `custom_treasury/services/treasury_movement_service.py:71-81`

Detalhe:

- se houver uma única moeda, retorna saldo na moeda da transação
- se houver mais de uma, retorna saldo consolidado em moeda da empresa
- há inclusive uma constante não usada indicando intenção de exigir filtro explícito:
  `custom_treasury/services/treasury_movement_service.py:11-13`

Impacto:

- a mesma API pode retornar naturezas diferentes de saldo
- isso aumenta risco de uso incorreto em telas, serviços e relatórios futuros

Recomendação:

- ou exigir moeda explícita em `compute_balance()`
- ou separar definitivamente `compute_balance_transaction_currency()` de `compute_balance_company_currency()`

### 2. Cobertura de testes ainda não cruzava retenção com multimoeda

Severidade encontrada: média

Status atual: corrigido

Existem testes de retenção mensal e existem testes de liquidação/pagamento em moeda estrangeira, mas não foi identificada cobertura cruzada entre esses dois aspectos.

Evidência:

- retenção:
  - `custom_account_receivable/tests/test_receivable.py:338-391`
  - `custom_account_payable/tests/test_payable.py:181-234`
- multimoeda:
  - `custom_account_receivable/tests/test_receivable.py:395-429`
  - `custom_account_payable/tests/test_payable.py:236-270`

Correção aplicada:

- foram adicionados cenários de teste em receber e pagar que misturam documentos do mês em moedas diferentes e validam a retenção pela moeda da empresa

### 3. Localização funcional ainda não está 100% consistente

Severidade: baixa

As mensagens de validação foram em grande parte padronizadas em português, mas ainda há partes visíveis da camada funcional em inglês.

Evidência:

- `custom_financial_base/models/financial_title_species.py:17-23`
- `custom_financial_base/models/financial_title_species.py:55-58`

Impacto:

- a experiência funcional fica parcialmente misturada entre português e inglês
- isso é menor que os problemas de regra de negócio, mas afeta acabamento do produto

## Lacunas funcionais ainda existentes

Além dos problemas confirmados, seguem lacunas importantes:

- não há apuração automática de ganho/perda cambial
- não há reavaliação cambial de saldos em aberto
- não há fluxo operacional completo para adiantamento de clientes
- não há fluxo operacional completo para adiantamento de fornecedores
- o mútuo entre empresas ainda está bloqueado para empresas com moedas-base diferentes

## Avaliação geral da arquitetura

### Pontos fortes

- modularização clara por domínio
- separação coerente entre obrigação financeira e tesouraria
- boa rastreabilidade via eventos, origem e estornos
- boa base para multimoeda
- boa capacidade de evolução sem acoplamento excessivo entre módulos

### Pontos que merecem reforço

- ainda existem pontos de integridade transversal a observar em futuras expansões
- o modelo de saldo precisa de API mais explícita para não gerar ambiguidade
- algumas funcionalidades de negócio importantes ainda estão só no nível cadastral

## Prioridade recomendada de correção

1. Definir e implementar o fluxo operacional de adiantamentos.
2. Revisar a API de saldo multimoeda para eliminar ambiguidade.
3. Completar a localização funcional restante em português.
4. Evoluir a camada cambial para ganho/perda e reavaliação de saldos.

## Conclusão

O projeto já está em um estágio avançado e tem uma base arquitetural boa. Não é um código desorganizado nem improvisado. Os principais problemas objetivos encontrados nesta análise foram corrigidos e a suíte integrada voltou a ficar verde.

Em termos práticos:

- há muita funcionalidade real já implementada;
- os erros objetivos encontrados nesta rodada foram corrigidos;
- a maior lacuna funcional relevante continua sendo adiantamento;
- a principal fragilidade arquitetural remanescente está na semântica do saldo multimoeda;
- a próxima evolução de maior impacto é a camada cambial completa.
