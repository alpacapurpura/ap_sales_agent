import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TenantDomainModel(Base):
    __tablename__ = "tenant_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    hostname = Column(String, nullable=False, index=True)
    domain_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending_verification")
    is_primary = Column(Boolean, nullable=False, default=False)
    cloudflare_hostname_id = Column(String, nullable=True)
    ssl_status = Column(String, nullable=True)
    verification_method = Column(String, nullable=True)
    verification_cname_target = Column(String, nullable=True)
    verification_txt_name = Column(String, nullable=True)
    verification_txt_value = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
