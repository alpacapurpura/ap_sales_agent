#!/usr/bin/env bash
# Verify Alembic migrations are idempotent on a clone of the dev DB schema.
# Implements the protocol from .claude/rules/backend-migrations.md.
#
# Pre-flight: requires `visionarias_postgres` + `visionarias_brain_dev` containers up.
# If either is down, exit code 0 with WARNING (graceful skip — caller decides).
#
# Steps (per backend-migrations.md):
#   1. Create migration_test DB
#   2. Dump schema from visionarias_logs into it
#   3. Stamp at current head revision
#   4. Re-run `alembic upgrade head` (must be a no-op = idempotent)
#   5. Drop migration_test
#
# Exit codes:
#   0 = pass (or graceful skip if containers down)
#   1 = idempotency violation (a migration tried to recreate something)
#   2 = setup failure (Postgres reachable but pg_dump/stamp/upgrade exploded)

set -euo pipefail

POSTGRES_CONTAINER="visionarias_postgres"
BRAIN_CONTAINER="visionarias_brain_dev"
SOURCE_DB="visionarias_logs"
TEST_DB="migration_test"

cleanup() {
    docker exec -t "$POSTGRES_CONTAINER" psql -U postgres -c "DROP DATABASE IF EXISTS $TEST_DB;" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# --- Pre-flight ---
if ! docker ps --format '{{.Names}}' | grep -qx "$POSTGRES_CONTAINER"; then
    echo "WARN: $POSTGRES_CONTAINER not running — skipping migration idempotency check"
    exit 0
fi
if ! docker ps --format '{{.Names}}' | grep -qx "$BRAIN_CONTAINER"; then
    echo "WARN: $BRAIN_CONTAINER not running — skipping migration idempotency check"
    exit 0
fi

echo "[1/5] creating $TEST_DB ..."
docker exec -t "$POSTGRES_CONTAINER" psql -U postgres -c "CREATE DATABASE $TEST_DB;" >/dev/null

echo "[2/5] dumping schema from $SOURCE_DB → $TEST_DB ..."
if ! docker exec "$POSTGRES_CONTAINER" bash -c "pg_dump -U postgres -s $SOURCE_DB | psql -U postgres -d $TEST_DB" >/dev/null 2>&1; then
    echo "FAIL: pg_dump/restore failed"
    exit 2
fi

CURRENT_REV=$(docker exec -t "$BRAIN_CONTAINER" bash -c "cd /app && alembic current 2>/dev/null | tail -1 | awk '{print \$1}'" | tr -d '\r\n ')
if [ -z "$CURRENT_REV" ] || [ "$CURRENT_REV" = "INFO" ]; then
    echo "FAIL: could not detect current alembic revision"
    exit 2
fi

echo "[3/5] stamping $TEST_DB at $CURRENT_REV ..."
if ! docker exec -t -e "POSTGRES_DB=$TEST_DB" "$BRAIN_CONTAINER" bash -c "cd /app && alembic stamp $CURRENT_REV" >/dev/null 2>&1; then
    echo "FAIL: alembic stamp failed"
    exit 2
fi

echo "[4/5] re-running alembic upgrade head (must be no-op) ..."
UPGRADE_OUT=$(docker exec -t -e "POSTGRES_DB=$TEST_DB" "$BRAIN_CONTAINER" bash -c "cd /app && alembic upgrade head" 2>&1)
UPGRADE_EXIT=$?

if [ $UPGRADE_EXIT -ne 0 ]; then
    echo "FAIL: alembic upgrade head failed on stamped clone — non-idempotent migration"
    echo "$UPGRADE_OUT" | tail -30
    exit 1
fi

# Detect migrations that ran (any "Running upgrade" line == something tried to mutate schema).
if echo "$UPGRADE_OUT" | grep -q "Running upgrade"; then
    echo "FAIL: idempotency violation — head already stamped but migrations re-ran:"
    echo "$UPGRADE_OUT" | grep "Running upgrade"
    exit 1
fi

echo "[5/5] cleanup ..."
echo "PASS: migrations idempotent at $CURRENT_REV"
