# Deploy Financeiro

## Escopo

- addons financeiros: `/proj_financeiro_odoo`
- deploy proprio: `/proj_financeiro_odoo/deploy`

Esse deploy nao depende dos addons do projeto EDI em `/proj_edi_odoo`
nem dos addons contabeis em `/proj_contabilidade`.
Como a suite financeira atual nao usa `queue_job`, este deploy fica enxuto:
`web`, `db` e `odoo-tests`.

## Arquivos

- `odoo-web.conf`
- `odoo-test.conf`
- `start-web.sh`
- `run-tests.sh`
- `docker-compose.yml`
- `.env.example`

## Subida manual

```bash
bash /proj_financeiro_odoo/deploy/start-web.sh
```

## Docker Compose

Copie o arquivo de ambiente:

```bash
cp /proj_financeiro_odoo/deploy/.env.example /proj_financeiro_odoo/deploy/.env
```

Subida:

```bash
docker compose -f /proj_financeiro_odoo/deploy/docker-compose.yml up -d
```

Parada:

```bash
docker compose -f /proj_financeiro_odoo/deploy/docker-compose.yml down
```

## Testes

Execucao local:

```bash
bash /proj_financeiro_odoo/deploy/run-tests.sh
```

Exemplo sobrescrevendo modulos:

```bash
ODOO_TEST_MODULES=custom_financial_base,custom_treasury bash /proj_financeiro_odoo/deploy/run-tests.sh
```

Via Docker Compose:

```bash
docker compose -f /proj_financeiro_odoo/deploy/docker-compose.yml --profile test run --rm odoo-tests
```
