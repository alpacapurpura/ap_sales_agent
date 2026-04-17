"""Currencies API — exposes the curated currency catalog.

Public, tenant-agnostic, cacheable. Mirrors the pattern of the
``/offer/archetypes/catalog`` and ``/brand/expert-business-types/catalog``
endpoints. Front-end pickers bind to this instead of hardcoding codes.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.shared.domain.currency_catalog import CURRENCY_CATALOG, CurrencyMetadata

router = APIRouter()


class CurrencyMetadataDTO(BaseModel):
    """DTO mirror of :class:`CurrencyMetadata`."""

    model_config = ConfigDict(frozen=True)

    code: str
    label_es: str
    symbol: str
    countries_es: list[str]
    decimal_digits: int

    @classmethod
    def from_domain(cls, metadata: CurrencyMetadata) -> CurrencyMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            code=metadata.code,
            label_es=metadata.label_es,
            symbol=metadata.symbol,
            countries_es=list(metadata.countries_es),
            decimal_digits=metadata.decimal_digits,
        )


class CurrencyCatalogResponse(BaseModel):
    """Versioned wrapper. Clients cache by the ``version`` string."""

    model_config = ConfigDict(frozen=True)

    version: str
    currencies: list[CurrencyMetadataDTO]


# Bump when ``currency_catalog.py`` changes materially (new entry, renamed
# label). Frontend caches by this version.
_CATALOG_VERSION = "2026-04-17"


@router.get(
    "/catalog",
    response_model=CurrencyCatalogResponse,
    summary="Curated currency catalog (public, cacheable)",
)
async def get_currency_catalog() -> CurrencyCatalogResponse:
    """Return locale-targeted currency metadata for UI pickers."""
    return CurrencyCatalogResponse(
        version=_CATALOG_VERSION,
        currencies=[CurrencyMetadataDTO.from_domain(m) for m in CURRENCY_CATALOG.values()],
    )
