# Financial Homologation Checklist

## Objetivo

Este roteiro serve para homologacao funcional da suite financeira no Odoo CE. O foco aqui nao e teste tecnico de codigo, e sim validacao operacional com usuario de negocio.

## Escopo

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

## Preparacao

### Pre-condicoes

- Banco de homologacao com os 10 addons instalados.
- Pelo menos 3 usuarios disponiveis:
  - usuario financeiro
  - gestor financeiro
  - usuario de cobranca
- Empresa, moeda e sequencias revisadas.
- Permissoes revisadas por grupo.

### Massa minima sugerida

- 4 portadores:
  - `CX001` caixa
  - `BC001` banco
  - `COB001` cobrador
  - `INT001` interno
- 2 contas financeiras
- 1 caixa
- 1 banco
- 1 conta bancaria
- 2 clientes
- 2 fornecedores
- 2 formas de pagamento
- 2 modalidades
- 1 cobrador

## Casos de Teste

### CT-01 Cadastros Base

Pre-condicao:
- usuario com acesso gerencial

Passos:
1. Criar portadores dos tipos `caixa`, `banco`, `cobrador` e `interno`.
2. Criar formas de pagamento.
3. Criar modalidades.
4. Criar historicos financeiros.
5. Criar motivos de movimento.
6. Criar parametros financeiros por empresa.

Resultado esperado:
- todos os cadastros gravam sem erro
- codigos unicos por empresa sao respeitados
- portador do cobrador fica disponivel para cobranca

Evidencia:
- capturas das telas de cadastro
- lista dos codigos criados

### CT-02 Tesouraria Basica

Pre-condicao:
- conta financeira criada
- portador interno criado

Passos:
1. Criar um movimento de entrada.
2. Criar um movimento de saida.
3. Consultar o saldo por conta.
4. Consultar o saldo por portador.

Resultado esperado:
- movimentos sao gravados
- saldo e derivado dos movimentos postados
- nao existe digitacao manual de saldo final

Evidencia:
- IDs dos movimentos
- saldo final esperado e obtido

### CT-03 Transferencia e Estorno

Pre-condicao:
- duas contas financeiras criadas

Passos:
1. Executar transferencia entre contas.
2. Verificar os dois movimentos gerados.
3. Estornar um movimento permitido.

Resultado esperado:
- transferencia gera saida e entrada
- estorno preserva historico do original
- saldo final reflete a operacao e o estorno

Evidencia:
- IDs dos movimentos gerados
- vinculo entre original e estorno

### CT-04 Operacao de Caixa

Pre-condicao:
- caixa com portador configurado

Passos:
1. Abrir sessao de caixa.
2. Registrar suprimento.
3. Registrar sangria.
4. Fechar sessao com valor exato.
5. Repetir fechamento com diferenca.

Resultado esperado:
- nao e possivel abrir segunda sessao para o mesmo caixa
- suprimento e sangria exigem sessao aberta
- diferenca e calculada corretamente
- quando parametrizado, motivo de diferenca e obrigatorio

Evidencia:
- numero da sessao
- valores de abertura, movimentacao e fechamento

### CT-05 Banco e Importacao de Extrato

Pre-condicao:
- banco e conta bancaria criados
- conta bancaria vinculada a conta financeira

Passos:
1. Vincular modalidades a conta bancaria.
2. Importar arquivo CSV de extrato.
3. Consultar saldo da tesouraria antes e depois.

Resultado esperado:
- extrato importa linhas corretamente
- linhas importadas ficam nao conciliadas
- importacao nao altera saldo automaticamente

Evidencia:
- arquivo usado
- quantidade de linhas importadas
- saldo antes e depois

### CT-06 Contas a Receber

Pre-condicao:
- cliente cadastrado

Passos:
1. Criar titulo a receber com parcelas.
2. Registrar liquidacao parcial.
3. Consultar saldo aberto da parcela.
4. Consultar saldo aberto do titulo.
5. Executar renegociacao.

Resultado esperado:
- parcela muda para `partial` ou `paid` conforme o caso
- titulo muda para `partial`, `paid` ou `renegotiated`
- renegociacao preserva vinculo com os titulos de origem

Evidencia:
- titulo original
- novo titulo renegociado
- saldos antes e depois

### CT-07 Contas a Pagar

Pre-condicao:
- fornecedor cadastrado

Passos:
1. Criar titulo a pagar com parcelas.
2. Criar programacao de pagamento.
3. Registrar pagamento parcial.
4. Consultar saldo aberto da parcela e do titulo.

Resultado esperado:
- programacao nao equivale a pagamento
- pagamento reduz saldo corretamente
- titulo e parcela refletem o estado operacional correto

Evidencia:
- numero do agendamento
- numero do pagamento
- saldos antes e depois

### CT-08 Integracao Financeira

Pre-condicao:
- receber e pagar com contas ou portadores configurados para integracao

Passos:
1. Aplicar uma liquidacao do receber.
2. Verificar evento e log de integracao.
3. Verificar movimento de entrada na tesouraria.
4. Aplicar um pagamento do pagar.
5. Verificar evento e log de integracao.
6. Verificar movimento de saida na tesouraria.

Resultado esperado:
- receber nao cria movimento direto fora da camada de integracao
- pagar nao cria movimento direto fora da camada de integracao
- evento, log e rastreabilidade ficam registrados

Evidencia:
- IDs do evento
- IDs dos movimentos
- origem e modelo vinculados

### CT-09 Conciliacao

Pre-condicao:
- extrato bancario importado
- movimento correspondente existente

Passos:
1. Criar conciliacao por conta bancaria e periodo.
2. Conciliar uma linha com movimento existente.
3. Tentar conciliar a mesma linha novamente.
4. Criar ajuste para linha divergente.
5. Finalizar conciliacao.

Resultado esperado:
- match atualiza status e bloqueia dupla conciliacao
- ajuste cria movimento proprio
- conciliacao nao finaliza com itens pendentes

Evidencia:
- linhas conciliadas
- linha ajustada
- movimento de ajuste

### CT-10 Cobranca em Campo

Pre-condicao:
- cobrador com portador do tipo `cobrador`
- titulo em aberto no contas a receber

Passos:
1. Criar roteiro de cobranca.
2. Atribuir parcela ao cobrador.
3. Registrar recebimento em campo.
4. Consultar saldo do portador do cobrador.
5. Executar prestacao de contas para conta financeira.
6. Repetir prestacao para caixa, se aplicavel.

Resultado esperado:
- atribuicao preserva historico
- recebimento em campo entra no portador do cobrador
- prestacao de contas transfere saldo para destino
- nao e permitida prestacao sem rastreabilidade das liquidacoes

Evidencia:
- numero do roteiro
- numero da atribuicao
- numero da liquidacao
- numeros dos movimentos de prestacao

### CT-11 Relatorios

Pre-condicao:
- massa dos testes anteriores criada

Passos:
1. Abrir extrato por conta.
2. Abrir extrato por portador.
3. Abrir saldo por conta.
4. Abrir saldo por portador.
5. Abrir fluxo de caixa realizado.
6. Abrir posicao em aberto do receber.
7. Abrir aging de vencidos.
8. Abrir historico de liquidacoes.
9. Abrir posicao em aberto do pagar.
10. Abrir agenda de pagamentos.
11. Abrir historico de pagamentos.
12. Abrir itens conciliados e divergentes.
13. Abrir prestacao de contas por cobrador.
14. Abrir titulos em rota.

Resultado esperado:
- todas as consultas abrem sem erro
- filtros por empresa funcionam
- relatorios nao alteram registros transacionais

Evidencia:
- filtros usados
- totalizadores exibidos
- confirmacao de que os dados nao foram alterados

### CT-12 Permissoes

Pre-condicao:
- usuarios com grupos distintos

Passos:
1. Entrar com usuario operacional.
2. Validar menus disponiveis.
3. Entrar com gestor.
4. Validar menus e cadastros gerenciais.
5. Entrar com usuario sem permissao financeira.
6. Confirmar restricoes.

Resultado esperado:
- cada perfil ve apenas o necessario
- relatorios respeitam empresa e grupos

Evidencia:
- usuarios usados
- menus visiveis por perfil

## Critérios de Aprovacao

- fluxos de negocio executados sem erro funcional
- saldos coerentes com os movimentos
- integracao entre receber, pagar e tesouraria validada
- conciliacao e cobranca rastreaveis
- relatorios somente leitura
- menus, nomes e comportamento aprovados pelo usuario funcional

## Registro de Pendencias

Use este formato para cada pendencia encontrada:

- `ID`
- `Modulo`
- `Cenario`
- `Passos para reproduzir`
- `Resultado obtido`
- `Resultado esperado`
- `Severidade`
- `Responsavel`

## Encerramento

- executar um fluxo completo de receber do inicio ao fim
- executar um fluxo completo de pagar do inicio ao fim
- validar nomenclaturas e permissões com o usuario chave
- consolidar pendencias antes de promover para producao
