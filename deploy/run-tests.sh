#!/usr/bin/env bash
set -eu

ODOO_DB_HOST="${ODOO_DB_HOST:-db}"
ODOO_DB_PORT="${ODOO_DB_PORT:-5432}"
ODOO_DB_USER="${ODOO_DB_USER:-odoo}"
ODOO_DB_PASSWORD="${ODOO_DB_PASSWORD:-odoo}"

ODOO_TEST_DB="${ODOO_TEST_DB:-odoo_test_financeiro}"
ODOO_TEST_MODULES="${ODOO_TEST_MODULES:-custom_financial_base,custom_treasury,custom_treasury_cash,custom_treasury_bank,custom_account_receivable,custom_account_payable,custom_financial_integration,custom_treasury_reconciliation,custom_account_receivable_collection,custom_financial_reports}"
ODOO_TEST_TAGS="${ODOO_TEST_TAGS:-}"
ODOO_TEST_HTTP_PORT="${ODOO_TEST_HTTP_PORT:-8090}"
ODOO_TEST_LOG_LEVEL="${ODOO_TEST_LOG_LEVEL:-info}"

args=(
  -c /proj_financeiro_odoo/deploy/odoo-test.conf
  --db_host "${ODOO_DB_HOST}"
  --db_port "${ODOO_DB_PORT}"
  --db_user "${ODOO_DB_USER}"
  --db_password "${ODOO_DB_PASSWORD}"
  --database "${ODOO_TEST_DB}"
  --init "${ODOO_TEST_MODULES}"
  --test-enable
  --stop-after-init
  --http-port "${ODOO_TEST_HTTP_PORT}"
  --log-level "${ODOO_TEST_LOG_LEVEL}"
)

if [ -n "${ODOO_TEST_TAGS}" ]; then
  args+=(
    --test-tags "${ODOO_TEST_TAGS}"
  )
fi

exec odoo "${args[@]}" "$@"
