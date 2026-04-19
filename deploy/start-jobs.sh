#!/usr/bin/env bash
set -eu

ODOO_DB_HOST="${ODOO_DB_HOST:-db}"
ODOO_DB_PORT="${ODOO_DB_PORT:-5432}"
ODOO_DB_USER="${ODOO_DB_USER:-odoo}"
ODOO_DB_PASSWORD="${ODOO_DB_PASSWORD:-odoo}"

exec odoo \
  -c /proj_edi_odoo/deploy/odoo-jobs.conf \
  --db_host "${ODOO_DB_HOST}" \
  --db_port "${ODOO_DB_PORT}" \
  --db_user "${ODOO_DB_USER}" \
  --db_password "${ODOO_DB_PASSWORD}"
