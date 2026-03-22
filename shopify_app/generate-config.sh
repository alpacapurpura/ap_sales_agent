#!/usr/bin/env bash
# Generates shopify.app.toml from environment variables.
# Usage:
#   ./generate-config.sh          # reads from ../.env (dev)
#   ./generate-config.sh prod     # reads from ../.env.prod

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_SUFFIX="${1:-}"
if [ "$ENV_SUFFIX" = "prod" ]; then
  ENV_FILE="$ROOT_DIR/.env.prod"
else
  ENV_FILE="$ROOT_DIR/.env"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found"
  exit 1
fi

# Source env vars (handle quotes and spaces)
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

TOML_FILE="$SCRIPT_DIR/shopify.app.toml"

cat > "$TOML_FILE" <<EOF
# AUTO-GENERATED from $ENV_FILE — do not edit manually.
# Run ./generate-config.sh [prod] to regenerate.

client_id = "$SHOPIFY_API_KEY"
name = "$SHOPIFY_APP_NAME"
application_url = "$DASHBOARD_DOMAIN"
embedded = true

[webhooks]
api_version = "2026-01"

[[webhooks.subscriptions]]
uri = "$SHOPIFY_APP_URL/api/v1/connections/shopify/compliance/customers/data_request"
compliance_topics = [ "customers/data_request" ]

[[webhooks.subscriptions]]
uri = "$SHOPIFY_APP_URL/api/v1/connections/shopify/compliance/customers/redact"
compliance_topics = [ "customers/redact" ]

[[webhooks.subscriptions]]
uri = "$SHOPIFY_APP_URL/api/v1/connections/shopify/compliance/shop/redact"
compliance_topics = [ "shop/redact" ]

[auth]
redirect_urls = [
  "https://dev-app.nicolify.com/api/auth/shopify/callback",
  "https://app.nicolify.com/api/auth/shopify/callback"
]

[access_scopes]
scopes = "write_customers,write_orders,read_analytics,read_customer_events,read_cart_transforms,read_all_cart_transforms,read_channels,read_checkouts,read_companies,read_custom_pixels,read_customers,read_customer_data_erasure,read_customer_merge,read_price_rules,read_discounts,read_discounts_allocator_functions,read_discovery,read_draft_orders,read_fulfillments,read_gift_card_transactions,read_gift_cards,read_inventory,read_inventory_shipments,read_inventory_shipments_received_items,read_locales,read_locations,read_marketing_integrated_campaigns,read_marketing_events,read_markets,read_markets_home,read_merchant_managed_fulfillment_orders,read_metaobject_definitions,read_metaobjects,read_online_store_navigation,read_online_store_pages,read_order_edits,read_orders,read_packing_slip_templates,read_payment_terms,read_payment_customizations,read_product_feeds,read_product_listings,read_products,read_publications,read_purchase_options,read_reports,read_resource_feedbacks,read_returns,read_script_tags,read_shipping,read_shopify_payments_payouts,read_shopify_payments_disputes,read_content,read_store_credit_account_transactions,read_third_party_fulfillment_orders,read_translations,read_pixels"

[pos]
embedded = false
EOF

echo "Generated $TOML_FILE from $ENV_FILE"
echo "  App:    $SHOPIFY_APP_NAME"
echo "  Key:    $SHOPIFY_API_KEY"
echo "  URLs:   $DASHBOARD_DOMAIN / $SHOPIFY_APP_URL"
