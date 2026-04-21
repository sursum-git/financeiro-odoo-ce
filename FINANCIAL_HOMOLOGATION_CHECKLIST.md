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

## Escopo Adicional de Multimoeda

- moeda por portador
- moeda por conta bancaria
- liquidacao em moeda estrangeira
- pagamento em moeda estrangeira
- integracao financeira preservando moeda da transacao
- caixa em moeda diferente da moeda-base
- conciliacao bloqueando moedas divergentes
- relatorios filtrados por moeda

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
- 2 moedas extras alem da moeda-base da empresa
- 1 portador em moeda estrangeira
- 1 conta bancaria em moeda estrangeira
- 1 cliente com titulo em moeda estrangeira
- 1 fornecedor com titulo em moeda estrangeira

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
7. Criar codigos de retencao por empresa.
8. Abrir um contato e associar mais de um codigo de retencao.
9. Informar percentual de retencao e contato recebedor em cada linha.

Resultado esperado:
- todos os cadastros gravam sem erro
- codigos unicos por empresa sao respeitados
- portador do cobrador fica disponivel para cobranca
- codigos de retencao ficam segregados por empresa
- um mesmo contato pode ter varias retencoes
- cada linha guarda percentual e contato recebedor do valor retido

Evidencia:
- capturas das telas de cadastro
- lista dos codigos criados

### CT-01A Retencoes por Contato

Pre-condicao:
- pelo menos 2 codigos de retencao criados para a mesma empresa
- contato principal cadastrado
- contatos recebedores cadastrados

Passos:
1. Abrir o cadastro do contato principal.
2. Inserir uma linha de retencao com o primeiro codigo.
3. Informar percentual de retencao.
4. Informar o contato que recebe o valor retido.
5. Inserir uma segunda linha com outro codigo.
6. Tentar repetir o mesmo codigo para a mesma empresa.
7. Tentar informar percentual maior que `100`.

Resultado esperado:
- o contato aceita varias linhas com codigos diferentes
- a mesma combinacao contato + empresa + codigo nao pode se repetir
- percentual invalido e bloqueado
- o contato recebedor fica gravado em cada linha

Evidencia:
- contato testado
- codigos associados
- percentual de cada linha
- mensagens de validacao exibidas

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

### CT-02A Tesouraria Multimoeda

Pre-condicao:
- portador em moeda estrangeira criado
- taxa cambial cadastrada para a data do teste

Passos:
1. Criar movimento de entrada em moeda estrangeira.
2. Criar movimento de saida em moeda estrangeira.
3. Consultar o valor do movimento na moeda da transacao.
4. Consultar o valor convertido na moeda da empresa.
5. Consultar saldo por moeda.

Resultado esperado:
- movimento grava a moeda da transacao corretamente
- taxa de cambio e valor convertido ficam preenchidos
- saldo por moeda nao mistura moedas diferentes
- saldo consolidado em moeda da empresa usa o valor convertido

Evidencia:
- moeda do movimento
- taxa usada
- valor na moeda da transacao
- valor na moeda da empresa

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

### CT-04A Caixa Multimoeda

Pre-condicao:
- caixa vinculado a portador em moeda estrangeira

Passos:
1. Abrir sessao de caixa em moeda estrangeira.
2. Registrar suprimento.
3. Registrar sangria.
4. Fechar sessao.
5. Criar prestacao de contas para outro portador da mesma moeda.

Resultado esperado:
- sessao usa a moeda do portador do caixa
- os movimentos da sessao sao criados na mesma moeda
- prestacao de contas nao aceita portador de destino em moeda diferente

Evidencia:
- moeda da sessao
- moedas dos movimentos
- validacao de moeda divergente, se testada

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

### CT-05A Banco Multimoeda

Pre-condicao:
- conta bancaria em moeda estrangeira criada
- taxa cambial cadastrada para a data do extrato

Passos:
1. Importar extrato da conta bancaria em moeda estrangeira.
2. Verificar a moeda das linhas importadas.
3. Verificar o valor convertido para a moeda da empresa.

Resultado esperado:
- linha de extrato usa a moeda da conta bancaria
- valor convertido fica disponivel para conciliacao e analise
- importacao continua sem alterar saldo automaticamente

Evidencia:
- moeda da conta bancaria
- moeda das linhas
- valor convertido das linhas

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

### CT-06A Receber Multimoeda

Pre-condicao:
- cliente com titulo em moeda estrangeira
- taxa cambial cadastrada

Passos:
1. Criar titulo a receber em moeda estrangeira.
2. Registrar liquidacao.
3. Verificar bruto, retido e liquido na moeda da transacao.
4. Verificar os mesmos totais na moeda da empresa.
5. Tentar criar liquidacao com parcelas de moedas diferentes.

Resultado esperado:
- liquidacao herda a moeda do titulo
- totais convertidos ficam preenchidos
- o sistema bloqueia mistura de moedas na mesma liquidacao

Evidencia:
- moeda do titulo
- moeda da liquidacao
- totais na moeda da transacao
- totais na moeda da empresa

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

### CT-07A Pagar Multimoeda

Pre-condicao:
- fornecedor com titulo em moeda estrangeira
- taxa cambial cadastrada

Passos:
1. Criar titulo a pagar em moeda estrangeira.
2. Registrar pagamento.
3. Verificar bruto, retido e liquido na moeda da transacao.
4. Verificar os mesmos totais na moeda da empresa.
5. Tentar criar pagamento com parcelas de moedas diferentes.

Resultado esperado:
- pagamento herda a moeda do titulo
- totais convertidos ficam preenchidos
- o sistema bloqueia mistura de moedas no mesmo pagamento

Evidencia:
- moeda do titulo
- moeda do pagamento
- totais na moeda da transacao
- totais na moeda da empresa

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

### CT-08A Integracao Financeira Multimoeda

Pre-condicao:
- receber ou pagar em moeda estrangeira com conta ou portador compativel

Passos:
1. Aplicar liquidacao em moeda estrangeira.
2. Verificar a moeda do movimento de tesouraria gerado.
3. Aplicar pagamento em moeda estrangeira.
4. Verificar a moeda do movimento de tesouraria gerado.

Resultado esperado:
- a integracao preserva a moeda da transacao
- o movimento de tesouraria guarda tambem o valor convertido

Evidencia:
- moeda do documento de origem
- moeda do movimento gerado
- valor na moeda da transacao
- valor na moeda da empresa

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

### CT-09A Conciliacao Multimoeda

Pre-condicao:
- extrato em moeda estrangeira
- movimento de tesouraria em moeda estrangeira
- movimento adicional em moeda diferente para teste negativo

Passos:
1. Conciliar extrato e movimento na mesma moeda.
2. Tentar conciliar extrato com movimento de moeda diferente.
3. Criar ajuste em linha de extrato estrangeira.

Resultado esperado:
- a conciliacao so aceita match na mesma moeda
- a tentativa com moeda divergente e bloqueada
- ajuste nasce na moeda do extrato

Evidencia:
- moeda da linha de extrato
- moeda do movimento conciliado
- mensagem de validacao no caso divergente

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

### CT-11A Relatorios Multimoeda

Pre-condicao:
- massa de movimentos, titulos e extratos em pelo menos duas moedas

Passos:
1. Abrir relatorios de tesouraria filtrando uma moeda especifica.
2. Abrir saldo por conta agrupado por moeda.
3. Abrir saldo por portador agrupado por moeda.
4. Abrir relatorios de receber e pagar filtrando moeda.
5. Abrir itens conciliados filtrando moeda.

Resultado esperado:
- filtros por moeda funcionam corretamente
- agrupamentos por moeda separam os valores da transacao
- tesouraria mostra tambem o valor convertido na moeda da empresa

Evidencia:
- filtros usados
- agrupamentos retornados
- totais por moeda

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
- regras de moeda aprovadas pelo usuario funcional
- cenarios multimoeda executados sem mistura indevida de moedas

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
- executar um fluxo completo multimoeda de receber do inicio ao fim
- executar um fluxo completo multimoeda de pagar do inicio ao fim
- validar nomenclaturas e permissões com o usuario chave
- consolidar pendencias antes de promover para producao
