"""Tracking Config domain definitions."""

from pydantic import BaseModel, ConfigDict


class TrackingConfig(BaseModel):
    """Schema for tracking config."""

    model_config = ConfigDict(from_attributes=True)

    # GTM-XXXX
    gtm_container_id: str | None = None
    # https://ss.example.com
    gtm_server_url: str | None = None
    # 123456789
    meta_pixel_id: str | None = None
    # G-XXXXXXXXXX
    ga_measurement_id: str | None = None
