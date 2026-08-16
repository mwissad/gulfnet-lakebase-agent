#!/usr/bin/env bash
# Grant App SP access to gulfnet OLTP schema (run after first deploy).
# Usage: PROFILE=fe-vm-mw-aws-demo APP=gulfnet-care-copilot ./scripts/grant_gulfnet_schema.sh
set -euo pipefail

PROFILE="${PROFILE:-fe-vm-mw-aws-demo}"
APP="${APP:-gulfnet-care-copilot}"
PROJECT="${PROJECT:-gulfnet-agent}"
BRANCH="${BRANCH:-production}"
ENDPOINT="${ENDPOINT:-primary}"
DB_NAME="${DB_NAME:-gulfnet}"
DBX="${DATABRICKS_CLI_PATH:-databricks}"
[[ -x /tmp/databricks_cli_new/databricks ]] && DBX=/tmp/databricks_cli_new/databricks

EP_PATH="projects/${PROJECT}/branches/${BRANCH}/endpoints/${ENDPOINT}"

SP=$($DBX apps get "$APP" -p "$PROFILE" -o json | python3 -c "import sys,json; print(json.load(sys.stdin).get('service_principal_client_id') or json.load(open('/dev/stdin')))" 2>/dev/null || true)
SP=$($DBX apps get "$APP" -p "$PROFILE" -o json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('service_principal_client_id') or d.get('service_principal_id') or '')")
if [[ -z "$SP" ]]; then
  echo "Could not resolve service_principal_client_id for app $APP"
  $DBX apps get "$APP" -p "$PROFILE" -o json | python3 -m json.tool | head -40
  exit 1
fi
echo "App SP client id: $SP"

HOST=$($DBX postgres list-endpoints "projects/${PROJECT}/branches/${BRANCH}" -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['status']['hosts']['host'])")
TOKEN=$($DBX postgres generate-database-credential "$EP_PATH" -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
EMAIL=$($DBX current-user me -p "$PROFILE" -o json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['userName'])")

# Postgres role for Apps SP is typically the client id with dashes replaced / as-is
ROLE="$SP"
export PGPASSWORD="$TOKEN"

psql "host=$HOST port=5432 dbname=${DB_NAME} user=$EMAIL sslmode=require" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${ROLE}') THEN
    CREATE ROLE "${ROLE}" LOGIN;
  END IF;
END
\$\$;

GRANT USAGE ON SCHEMA gulfnet TO "${ROLE}";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gulfnet TO "${ROLE}";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gulfnet TO "${ROLE}";
ALTER DEFAULT PRIVILEGES IN SCHEMA gulfnet GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "${ROLE}";
ALTER DEFAULT PRIVILEGES IN SCHEMA gulfnet GRANT USAGE, SELECT ON SEQUENCES TO "${ROLE}";
SQL

echo "Granted gulfnet schema privileges to ${ROLE}"
