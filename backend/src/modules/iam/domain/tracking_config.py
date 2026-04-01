from typing import Optional
from pydantic import BaseModel, ConfigDict


class TrackingConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # GTM-XXXX
    gtm_container_id: Optional[str] = None
    # https://ss.example.com
    gtm_server_url: Optional[str] = None
    # 123456789
    meta_pixel_id: Optional[str] = None
    # G-XXXXXXXXXX
    ga_measurement_id: Optional[str] = None
