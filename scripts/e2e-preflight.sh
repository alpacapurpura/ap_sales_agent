#!/usr/bin/env bash
# E2E Preflight Check — run BEFORE any Playwright test
# Catches the 3 most common E2E failures before they waste 2+ minutes:
#   1. Frontend container down or unhealthy (500 errors)
#   2. Missing npm dependencies (Module not found)
#   3. Clerk auth state expired or missing
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

echo "=== E2E Preflight Check ==="

# 1. Docker containers running
echo -n "Checking Docker containers... "
if ! docker compose ps --format "{{.Name}} {{.Status}}" 2>/dev/null | grep -q "visionarias_client_dev.*Up"; then
    echo -e "${RED}FAIL${NC} — frontend container not running"
    echo "  Fix: docker compose up -d"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# 2. Frontend responds 200 (not 500)
echo -n "Checking frontend responds 200... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}FAIL${NC} — got HTTP $HTTP_CODE"

    # Check for Module not found (most common cause of 500)
    MODULE_ERROR=$(docker logs visionarias_client_dev 2>&1 | grep "Module not found" | tail -1 || true)
    if [ -n "$MODULE_ERROR" ]; then
        # Extract missing module name
        MISSING=$(echo "$MODULE_ERROR" | grep -oP "Can't resolve '\K[^']+")
        echo -e "  ${YELLOW}Cause: Missing module '$MISSING'${NC}"
        echo "  Fix: docker exec visionarias_client_dev npm install $MISSING"
        echo "       docker compose restart client_dashboard_dev"
    else
        echo "  Fix: docker compose restart client_dashboard_dev"
        echo "       Wait 20s, then retry"
    fi
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# 3. No Module not found in recent logs (even if 200 — some routes may fail)
echo -n "Checking for module errors in logs... "
MODULE_ERRORS=$(docker logs visionarias_client_dev --tail 50 2>&1 | grep -c "Module not found" || true)
if [ "$MODULE_ERRORS" -gt "0" ]; then
    echo -e "${YELLOW}WARN${NC} — $MODULE_ERRORS 'Module not found' in recent logs"
    MISSING=$(docker logs visionarias_client_dev 2>&1 | grep "Module not found" | grep -oP "Can't resolve '\K[^']+" | sort -u | head -3)
    echo "  Missing: $MISSING"
    echo "  Fix: docker exec visionarias_client_dev npm install $MISSING"
else
    echo -e "${GREEN}OK${NC}"
fi

# 4. Clerk auth state freshness (4h hard limit — Clerk JWT + cf_bm cookie expire)
echo -n "Checking Clerk auth state... "
AUTH_FILE="frontend/playwright/.clerk/user.json"
STALE_HOURS=4
if [ ! -f "$AUTH_FILE" ]; then
    echo -e "${GREEN}OK${NC} — no cached state, setup project will create one"
else
    AGE_MIN=$(( ($(date +%s) - $(stat -c %Y "$AUTH_FILE")) / 60 ))
    if [ "$AGE_MIN" -gt $((STALE_HOURS * 60)) ]; then
        echo -e "${YELLOW}STALE${NC} — auth state is ${AGE_MIN}min old (>${STALE_HOURS}h limit)"
        echo "  Auto-wiping; setup project will re-authenticate."
        rm -f "$AUTH_FILE"
    else
        echo -e "${GREEN}OK${NC} — ${AGE_MIN}min old"
    fi
fi

# 5. Required env vars
echo -n "Checking E2E env vars... "
MISSING_VARS=""
for VAR in E2E_CLERK_USER_EMAIL E2E_CLERK_USER_PASSWORD E2E_TENANT_ID NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY CLERK_SECRET_KEY; do
    if ! grep -q "^${VAR}=" .env 2>/dev/null; then
        MISSING_VARS="$MISSING_VARS $VAR"
    fi
done
if [ -n "$MISSING_VARS" ]; then
    echo -e "${RED}FAIL${NC} — missing in .env:$MISSING_VARS"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# 6. Export E2E_BASE_URL reminder
echo -n "Checking E2E_BASE_URL... "
if [ -z "${E2E_BASE_URL:-}" ]; then
    echo -e "${YELLOW}HINT${NC} — set E2E_BASE_URL=http://localhost:3000 to skip webServer startup"
else
    echo -e "${GREEN}OK${NC} — $E2E_BASE_URL"
fi

echo ""
if [ "$ERRORS" -gt "0" ]; then
    echo -e "${RED}=== PREFLIGHT FAILED ($ERRORS errors) ===${NC}"
    echo "Fix the errors above before running Playwright."
    exit 1
else
    echo -e "${GREEN}=== PREFLIGHT PASSED ===${NC}"
    exit 0
fi
