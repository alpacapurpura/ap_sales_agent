#!/usr/bin/env bash
# Validates that the TOML files match the env files.
# The TOMLs are now manually maintained (not auto-generated) since we have
# 2 separate Shopify apps (nicolify-dev + nicolify-prod).
#
# Usage:
#   ./generate-config.sh          # validates dev config
#   ./generate-config.sh prod     # validates prod config
#
# Shopify CLI commands:
#   Development:  cd shopify_app && npx shopify app dev
#   Deploy prod:  cd shopify_app && npx shopify app deploy --config prod

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_SUFFIX="${1:-}"
if [ "$ENV_SUFFIX" = "prod" ]; then
  ENV_FILE="$ROOT_DIR/.env.prod"
  TOML_FILE="$SCRIPT_DIR/shopify.app.prod.toml"
  CONFIG_NAME="prod"
else
  ENV_FILE="$ROOT_DIR/.env"
  TOML_FILE="$SCRIPT_DIR/shopify.app.toml"
  CONFIG_NAME="dev (default)"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found"
  exit 1
fi

if [ ! -f "$TOML_FILE" ]; then
  echo "Error: $TOML_FILE not found"
  exit 1
fi

# Source env vars
set -a
source <(grep -E '^(SHOPIFY_|DASHBOARD_DOMAIN=)' "$ENV_FILE" | sed 's/\r$//')
set +a

# Validate required vars
for var in SHOPIFY_API_KEY SHOPIFY_APP_NAME SHOPIFY_APP_URL DASHBOARD_DOMAIN; do
  if [ -z "${!var:-}" ]; then
    echo "Error: $var not set in $ENV_FILE"
    exit 1
  fi
done

# Validate TOML matches env
echo "=== Shopify Config Validation ($CONFIG_NAME) ==="
echo "  Env file:  $ENV_FILE"
echo "  TOML file: $TOML_FILE"
echo ""
echo "  App name:    $SHOPIFY_APP_NAME"
echo "  Client ID:   $SHOPIFY_API_KEY"
echo "  App URL:     $SHOPIFY_APP_URL"
echo "  Dashboard:   $DASHBOARD_DOMAIN"
echo ""

# Check client_id matches
TOML_CLIENT_ID=$(grep 'client_id' "$TOML_FILE" | head -1 | sed 's/.*"\(.*\)".*/\1/')
if [ "$TOML_CLIENT_ID" != "$SHOPIFY_API_KEY" ]; then
  echo "WARNING: client_id mismatch!"
  echo "  TOML:  $TOML_CLIENT_ID"
  echo "  .env:  $SHOPIFY_API_KEY"
  exit 1
fi

# Check application_url matches DASHBOARD_DOMAIN
TOML_APP_URL=$(grep 'application_url' "$TOML_FILE" | head -1 | sed 's/.*"\(.*\)".*/\1/')
if [ "$TOML_APP_URL" != "$DASHBOARD_DOMAIN" ]; then
  echo "WARNING: application_url mismatch!"
  echo "  TOML:  $TOML_APP_URL"
  echo "  .env:  $DASHBOARD_DOMAIN"
  exit 1
fi

echo "All checks passed!"
echo ""
echo "Next steps:"
if [ "$ENV_SUFFIX" = "prod" ]; then
  echo "  Deploy to Shopify:  cd shopify_app && npx shopify app deploy --config prod"
else
  echo "  Start dev server:   cd shopify_app && npx shopify app dev"
fi
