# Financial Homologation Checklist

## Preparacao
- Instalar os 10 addons financeiros no mesmo banco de homologacao.
- Validar grupos de acesso por perfil: base, tesouraria, caixa, banco, receber, pagar, conciliacao, cobranca e relatorios.
- Confirmar empresa padrao, moeda e usuarios de teste.

## Cadastros Base
- Criar portadores dos tipos `caixa`, `banco`, `cobrador` e `interno`.
- Criar formas de pagamento e modalidades.
- Criar historicos e motivos de movimento.
- Criar parametros financeiros por empresa.

## Tesouraria
- Criar conta financeira.
- Lancar movimento de entrada e saida.
- Confirmar saldo derivado por conta e por portador.
- Executar transferencia entre contas e conferir os dois movimentos gerados.
- Estornar um movimento e conferir rastreabilidade.

## Caixa
- Criar caixa com portador.
- Abrir sessao de caixa.
- Registrar suprimento e sangria.
- Fechar sessao com e sem diferenca.
- Validar exigencia de motivo de diferenca, quando aplicavel.

## Banco
- Criar banco e conta bancaria vinculada a conta de tesouraria.
- Vincular modalidades a conta bancaria.
- Importar extrato CSV.
- Confirmar que a importacao do extrato nao altera saldo sozinha.

## Contas a Receber
- Criar titulo com parcelas.
- Registrar liquidacao parcial.
- Validar atualizacao de saldo aberto da parcela e do titulo.
- Executar renegociacao e validar o vinculo com os titulos originais.

## Contas a Pagar
- Criar titulo com parcelas.
- Criar programacao de pagamento.
- Registrar pagamento parcial.
- Validar atualizacao de saldo aberto da parcela e do titulo.

## Integracao Financeira
- Aplicar liquidacao do receber com conta ou portador destino.
- Confirmar criacao automatica do movimento de entrada na tesouraria.
- Aplicar pagamento do pagar com conta ou portador origem.
- Confirmar criacao automatica do movimento de saida na tesouraria.
- Validar evento e log de integracao.

## Conciliacao
- Criar conciliacao para conta bancaria e periodo.
- Conciliar item de extrato com movimento existente.
- Criar ajuste para item divergente.
- Validar bloqueio de dupla conciliacao.
- Finalizar conciliacao sem itens pendentes.

## Cobranca
- Criar cobrador com portador do tipo `cobrador`.
- Criar roteiro e atribuir parcelas ao cobrador.
- Registrar recebimento em campo.
- Confirmar entrada financeira no portador do cobrador.
- Executar prestacao de contas para conta ou caixa destino.
- Confirmar saida do portador do cobrador e entrada no destino.

## Relatorios
- Abrir extrato por conta e por portador.
- Abrir saldo por conta e por portador.
- Abrir fluxo de caixa realizado.
- Abrir posicao em aberto do receber e aging de vencidos.
- Abrir posicao em aberto do pagar, agenda e historico.
- Abrir itens conciliados, divergentes, prestacoes por cobrador e titulos em rota.
- Confirmar que os relatorios nao alteram dados transacionais.

## Encerramento
- Executar smoke test de ponta a ponta em um fluxo real de receber e outro de pagar.
- Validar nomenclaturas, menus e permissoes com o usuario funcional.
- Registrar pendencias de negocio antes de promover para producao.
