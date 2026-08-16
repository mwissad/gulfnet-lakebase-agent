#!/usr/bin/env bash
# Provision / apply GulfNet schema on Lakebase Autoscaling.
# Usage: PROFILE=fe-vm-mw-aws-demo ./scripts/setup_lakebase.sh
set -euo pipefail

PROFILE="${PROFILE:-fe-vm-mw-aws-demo}"
PROJECT="${PROJECT:-gulfnet-agent}"
BRANCH="${BRANCH:-production}"
ENDPOINT="${ENDPOINT:-primary}"
DB_NAME="${DB_NAME:-gulfnet}"
DBX="${DBX:-databricks}"

# Prefer newer CLI if present
if [[ -x /tmp/databricks_cli_new/databricks ]]; then
  DBX=/tmp/databricks_cli_new/databricks
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EP_PATH="projects/${PROJECT}/branches/${BRANCH}/endpoints/${ENDPOINT}"

echo "==> Resolving endpoint host"
HOST=$($DBX postgres list-endpoints "projects/${PROJECT}/branches/${BRANCH}" -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['status']['hosts']['host'])")

echo "==> Generating OAuth credential"
TOKEN=$($DBX postgres generate-database-credential "$EP_PATH" -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

EMAIL=$($DBX current-user me -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['userName'])")

export PGPASSWORD="$TOKEN"
PSQL=(psql "host=$HOST port=5432 dbname=databricks_postgres user=$EMAIL sslmode=require")

echo "==> Ensuring database ${DB_NAME}"
"${PSQL[@]}" -v ON_ERROR_STOP=1 -c "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || "${PSQL[@]}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_NAME};"

PSQL_APP=(psql "host=$HOST port=5432 dbname=${DB_NAME} user=$EMAIL sslmode=require")

echo "==> Applying schema"
"${PSQL_APP[@]}" -v ON_ERROR_STOP=1 -f "$ROOT/sql/01_schema.sql"
echo "==> Seeding data"
"${PSQL_APP[@]}" -v ON_ERROR_STOP=1 -f "$ROOT/sql/02_seed.sql"

echo "==> Done. Host=${HOST} db=${DB_NAME} project=${PROJECT}"
echo "Export for .env:"
echo "  LAKEBASE_AUTOSCALING_PROJECT=${PROJECT}"
echo "  LAKEBASE_AUTOSCALING_BRANCH=${BRANCH}"
echo "  LAKEBASE_AUTOSCALING_ENDPOINT=${EP_PATH}"
echo "  GULFNET_DATABASE=${DB_NAME}"
