"""CountryBlock Policy — PM Q3 production-grade country blocking.

Resolution chain (lead.country preferred — PM Q3):
1. lead.country (explicit ISO 3166-1 alpha-2 — preferred).
2. Phone E.164 prefix heuristic (whatsapp/telegram only).
3. None / unknown → PASS (allow by default per PR-2 semantics).

Default env: COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST="" (empty → effectively no-op).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import os
import re
from typing import Any
from uuid import UUID

import structlog
from luana_core_compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)

# E.164 prefix → ISO 3166-1 alpha-2 (partial, common LATAM + high-risk)
# Only used as fallback when lead.country is NULL.
PHONE_PREFIX_MAP: dict[str, str] = {
    "+53": "CU",
    "+98": "IR",
    "+850": "KP",
    "+963": "SY",
    "+52": "MX",
    "+51": "PE",
    "+57": "CO",
    "+56": "CL",
    "+54": "AR",
    "+55": "BR",
    "+593": "EC",
    "+591": "BO",
    "+595": "PY",
    "+598": "UY",
    "+507": "PA",
    "+506": "CR",
    "+502": "GT",
    "+504": "HN",
    "+503": "SV",
    "+505": "NI",
    "+1": "US",  # US/Canada — broad prefix, only used as last resort
}


def _lookup_phone_prefix(identifier: str) -> str | None:
    """Heuristic E.164 prefix → country ISO.

    Returns ISO alpha-2 or None if no match.
    Only used for whatsapp/telegram channels.
    """
    # Normalize: strip spaces, ensure starts with +
    normalized = re.sub(r"[\s\-()]", "", identifier)
    if not normalized.startswith("+"):
        return None
    # Try longest prefix first (e.g. +850 before +85)
    for prefix in sorted(PHONE_PREFIX_MAP, key=len, reverse=True):
        if normalized.startswith(prefix):
            return PHONE_PREFIX_MAP[prefix]
    return None


class CountryBlockPolicy:
    """All channels: verify country is not in block list.

    PM Q3: lead.country field is the preferred signal.
    Fallback to E.164 phone prefix heuristic for whatsapp/telegram.
    Unknown country → PASS (permissive default).

    Default block list is EMPTY (Chris activates when legal requires).
    """

    name: str = "country_block"
    _PHONE_CHANNELS = frozenset({"whatsapp", "telegram"})

    def __init__(self, lead_country_reader: Any | None = None) -> None:
        """Bind to lead_country_reader (optional duck-typed async callable).

        lead_country_reader.get_lead_country(tenant_id, lead_id) -> str | None
        If None, only phone prefix heuristic is used.
        """
        self._lead_country_reader = lead_country_reader
        self._block_list = self._load_block_list()

    def _load_block_list(self) -> frozenset[str]:
        """Load country block list from env var. Default empty."""
        raw = os.getenv("COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST", "")
        if not raw.strip():
            return frozenset()
        return frozenset(c.strip().upper() for c in raw.split(",") if c.strip())

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Evaluate country block policy."""
        # Empty block list → pass immediately (default PR-2 behavior)
        if not self._block_list:
            return CheckResult(allowed=True)

        # Resolve country via fallback chain (PM Q3)
        country_iso, country_source = await self._resolve_country(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel=channel,
            identifier=identifier,
        )

        if country_iso is None:
            # Unknown country → allow by default
            return CheckResult(
                allowed=True,
                evidence={
                    "country_iso": None,
                    "country_source": "unknown",
                },
            )

        if country_iso in self._block_list:
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason=f"País '{country_iso}' no permitido para comunicaciones",
                evidence={
                    "country_iso": country_iso,
                    "country_source": country_source,
                    "block_list_source": "COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST",
                },
            )

        return CheckResult(
            allowed=True,
            evidence={
                "country_iso": country_iso,
                "country_source": country_source,
            },
        )

    async def _resolve_country(
        self, *, tenant_id: UUID, lead_id: UUID, channel: str, identifier: str
    ) -> tuple[str | None, str]:
        """Resolve country via fallback chain.

        Returns (country_iso | None, source_label).
        source_label: "lead_field" | "phone_prefix" | "unknown"
        """
        # 1. Preferred: lead.country field (explicit ISO alpha-2)
        if self._lead_country_reader is not None:
            try:
                country = await self._lead_country_reader.get_lead_country(tenant_id=tenant_id, lead_id=lead_id)
                if country:
                    return country.upper(), "lead_field"
            except Exception as exc:  # noqa: BLE001 — graceful degradation
                logger.warning(
                    "country_block_lead_reader_error",
                    tenant_id=str(tenant_id),
                    lead_id=str(lead_id),
                    error=str(exc),
                )

        # 2. Phone E.164 prefix heuristic (whatsapp/telegram only)
        if channel in self._PHONE_CHANNELS:
            country = _lookup_phone_prefix(identifier)
            if country:
                return country, "phone_prefix"

        # 3. Unknown
        return None, "unknown"
