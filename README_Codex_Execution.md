# COMO EXECUTAR NO CODEX

## Objetivo
Usar estes arquivos como especificação por fases para construir os addons financeiros no Odoo CE.

## Procedimento obrigatório por fase

1. Ler o arquivo `00_overview.md`
2. Ler o arquivo da fase atual
3. Criar ou atualizar o addon correspondente
4. Implementar models, views, security, data e tests
5. Instalar o módulo no ambiente Odoo
6. Executar os testes da fase
7. Corrigir falhas
8. Só depois seguir para a próxima fase

## Instruções de implementação

- Seguir boas práticas de Odoo
- Evitar lógica duplicada
- Criar serviços reutilizáveis para regras centrais
- Não concentrar lógica complexa em views
- Não acoplar receber/pagar diretamente à tesouraria sem a camada de integração
- Criar testes automatizados de regressão em cada addon
- Não usar exclusão física como fluxo normal para registros financeiros
- Respeitar multiempresa
- Respeitar segurança por grupo
- Usar nomes técnicos consistentes

## Saída esperada do Codex a cada fase

- Código do addon
- Testes automatizados
- Instalação validada
- Correções aplicadas
- Resumo do que foi implementado
- Lista de pendências, se houver

## Observação
Se alguma fase exigir pequeno ajuste na anterior, o Codex pode corrigir a fase anterior, desde que preserve compatibilidade e registre a mudança.
