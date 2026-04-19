# Deploy Odoo + Queue Job

## Topologia recomendada

- `web`: atende interface HTTP e mantém cron leve
- `jobs`: consome a fila do `queue_job` com canais dedicados ao EDI

## Arquivos

- `odoo-web.conf`
- `odoo-jobs.conf`
- `odoo-test.conf`
- `start-web.sh`
- `start-jobs.sh`
- `run-tests.sh`

## Subida manual

```bash
bash /proj_edi_odoo/deploy/start-web.sh
```

```bash
bash /proj_edi_odoo/deploy/start-jobs.sh
```

## Docker Compose

Arquivo:

- `docker-compose.yml`
- `.env.example`

Copie o arquivo de exemplo:

```bash
cp /proj_edi_odoo/deploy/.env.example /proj_edi_odoo/deploy/.env
```

Subida:

```bash
docker compose -f /proj_edi_odoo/deploy/docker-compose.yml up -d
```

Parada:

```bash
docker compose -f /proj_edi_odoo/deploy/docker-compose.yml down
```

Serviços:

- `db`
- `odoo-web`
- `odoo-jobs`
- `odoo-tests` (perfil `test`)

Variáveis parametrizadas:

- banco: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- conexão Odoo: `ODOO_DB_HOST`, `ODOO_DB_PORT`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD`
- portas: `WEB_PORT`, `JOBS_PORT`
- nomes de container: `POSTGRES_CONTAINER`, `ODOO_WEB_CONTAINER`, `ODOO_JOBS_CONTAINER`
- testes: `ODOO_TEST_DB`, `ODOO_TEST_MODULES`, `ODOO_TEST_TAGS`, `ODOO_TEST_HTTP_PORT`, `ODOO_TESTS_CONTAINER`

## Testes Odoo

Execução local no container Odoo:

```bash
bash /proj_edi_odoo/deploy/run-tests.sh
```

Exemplo filtrando por tags:

```bash
ODOO_TEST_TAGS=/edi_framework bash /proj_edi_odoo/deploy/run-tests.sh
```

Exemplo sobrescrevendo módulos:

```bash
ODOO_TEST_MODULES=edi_framework bash /proj_edi_odoo/deploy/run-tests.sh
```

Via Docker Compose:

```bash
docker compose -f /proj_edi_odoo/deploy/docker-compose.yml --profile test run --rm odoo-tests
```

## Canais configurados

```ini
root:1
root.edi:1
root.edi.api:1
root.edi.file:1
```

## Observações

- `server_wide_modules = web,queue_job` precisa estar presente nos dois nós.
- O nó `jobs` fica com `max_cron_threads = 0` para não misturar cron com fila.
- O canal `root.edi:1` mantém o EDI conservador no início; aumente só após medir.
- os arquivos `.conf` não carregam mais credenciais fixas de banco; isso agora entra pelos scripts `start-web.sh` e `start-jobs.sh`
- os testes usam `workers = 0`, `--test-enable` e `--stop-after-init` para manter a execução determinística
