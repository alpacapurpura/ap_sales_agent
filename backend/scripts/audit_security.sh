#!/usr/bin/env bash
# Run pip-audit with an explicit allowlist of currently-known CVEs.
#
# Goal: block ANY new CVE that appears, while we work down the documented backlog.
# When you upgrade a package and clear a CVE: remove its line from ALLOWED below.
# Skill /test-backend treats any non-zero exit as a blocker.
#
# Usage:
#   bash scripts/audit_security.sh
#
# Exit codes:
#   0 = no new CVEs (allowlisted CVEs may still be present)
#   1 = new CVE detected outside allowlist OR pip-audit itself failed

set -euo pipefail

cd "$(dirname "$0")/.."

# CVE allowlist — measured 2026-04-28. Each line: <CVE/GHSA/PYSEC ID>  # package@version  reason
ALLOWED=(
    "GHSA-r7w7-9xr2-qq2r"   # langchain-openai 1.1.11 — SSRF/TOCTOU (low impact: response body never returned)
    "GHSA-fv5p-p927-qmxr"   # langchain-text-splitters 1.1.1 — SSRF redirect bypass
    "GHSA-rr7j-v2q5-chgv"   # langsmith 0.7.22 — streaming token redaction bypass
    "CVE-2026-41066"        # lxml 6.0.2 — XML local file read default
    "CVE-2026-40192"        # pillow 12.1.1 — FITS decompression bomb
    "CVE-2026-3219"         # pip 26.0.1 — concatenated tar+zip ambiguity
    "PYSEC-2022-42969"      # py 1.11.0 — ReDoS, transitive via pytest, no fix
    "CVE-2026-40260"        # pypdf 6.9.2 — XMP memory bomb
    "GHSA-jj6c-8h6c-hppx"   # pypdf 6.9.2 — xref Size large runtime
    "GHSA-4pxv-j86v-mhcw"   # pypdf 6.9.2 — incremental Size runtime
    "GHSA-7gw9-cf7v-778f"   # pypdf 6.9.2 — FlateDecode predictor RAM
    "GHSA-x284-j5p8-9c5p"   # pypdf 6.9.2 — FlateDecode image RAM
    "CVE-2025-71176"        # pytest 9.0.2 — /tmp/pytest-of-{user} privilege bug
    "CVE-2026-40347"        # python-multipart 0.0.22 — multipart preamble DoS
)

IGNORE_FLAGS=()
for id in "${ALLOWED[@]}"; do
    IGNORE_FLAGS+=("--ignore-vuln" "$id")
done

OUT=$(.venv/bin/pip-audit --strict --desc "${IGNORE_FLAGS[@]}" 2>&1) || EXIT=$?
EXIT=${EXIT:-0}

if [ $EXIT -eq 0 ]; then
    echo "PASS: no new CVEs (${#ALLOWED[@]} allowlisted)"
    exit 0
fi

echo "FAIL: pip-audit detected CVE(s) outside allowlist"
echo "---"
echo "$OUT"
echo "---"
echo "Action: upgrade the affected package, OR (if no fix exists) add the ID to ALLOWED in this script with justification."
exit 1
