#!/usr/bin/env bash
# test-webhook.sh — verifica el pipeline completo Sentry → Worker → Slack
#
# Uso:
#   SENTRY_WEBHOOK_SECRET=<clientSecret de la Internal Integration> ./test-webhook.sh
#
# El clientSecret está en:
#   Sentry UI → Settings → Integrations → Internal Integrations → "Slack Alerts Worker" → Credentials
#
# Si el script recibe HTTP 200 Y llega un mensaje a Slack, el pipeline funciona.
# Si recibe HTTP 401, el SENTRY_WEBHOOK_SECRET del worker es incorrecto.

set -euo pipefail

WORKER_URL="https://sentry-slack-alerts.late-butterfly-22c0.workers.dev"
SECRET="${SENTRY_WEBHOOK_SECRET:?'Falta SENTRY_WEBHOOK_SECRET. Ej: SENTRY_WEBHOOK_SECRET=xxx ./test-webhook.sh'}"

# Payload mínimo que simula un issue nuevo HIGH priority
BODY=$(cat <<'EOF'
{
  "action": "created",
  "data": {
    "issue": {
      "id": "test-001",
      "title": "[TEST] Pipeline Sentry → Slack funcionando correctamente",
      "culprit": "test-webhook.sh",
      "permalink": "https://alpaca-purpura-to.sentry.io/issues/test-001/",
      "shortId": "NICOLIFY-BACKEND-TEST",
      "status": "unresolved",
      "count": "1",
      "userCount": 0,
      "firstSeen": "2026-04-02T00:00:00.000000Z",
      "lastSeen": "2026-04-02T00:00:00.000000Z",
      "tags": [
        {"key": "environment", "value": "production"},
        {"key": "tenant_id", "value": "test-tenant"}
      ],
      "priority": "high",
      "project": {
        "id": "test",
        "name": "nicolify-backend",
        "slug": "nicolify-backend"
      }
    }
  }
}
EOF
)

# Calcular HMAC-SHA256 de la misma forma que Sentry
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

echo "→ Enviando test webhook al worker..."
echo "  URL:       $WORKER_URL"
echo "  Signature: ${SIGNATURE:0:16}..."

HTTP_STATUS=$(curl -s -o /tmp/worker_response.txt -w "%{http_code}" \
  -X POST "$WORKER_URL" \
  -H "Content-Type: application/json" \
  -H "sentry-hook-signature: $SIGNATURE" \
  -d "$BODY")

RESPONSE=$(cat /tmp/worker_response.txt)

echo ""
echo "← HTTP $HTTP_STATUS: $RESPONSE"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ Worker aceptó el webhook. Verifica Slack — debería haber llegado un mensaje HIGH priority."
elif [ "$HTTP_STATUS" = "401" ]; then
  echo "❌ 401 Unauthorized — el SENTRY_WEBHOOK_SECRET del worker NO coincide con el clientSecret de Sentry."
  echo ""
  echo "Para corregirlo:"
  echo "  1. Ir a: Sentry → Settings → Integrations → Internal Integrations → 'Slack Alerts Worker'"
  echo "  2. Copiar el 'Client Secret'"
  echo "  3. Ejecutar: cd workers/sentry-slack-alerts && npx wrangler secret put SENTRY_WEBHOOK_SECRET"
  echo "  4. Pegar el Client Secret cuando wrangler lo solicite"
  echo "  5. Volver a ejecutar este script para confirmar"
elif [ "$HTTP_STATUS" = "502" ]; then
  echo "⚠️  502 — el worker llamó a Slack pero Slack rechazó la request (SLACK_WEBHOOK_URL incorrecta)."
else
  echo "⚠️  HTTP $HTTP_STATUS inesperado."
fi
