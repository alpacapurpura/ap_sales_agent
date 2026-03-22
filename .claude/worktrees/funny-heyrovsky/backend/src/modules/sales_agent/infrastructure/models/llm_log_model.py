from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base

class LLMLog(Base):
    __tablename__ = "llm_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("agent_traces.id"), nullable=True)
    
    model = Column(String, nullable=False)
    prompt_template = Column(String, nullable=True)
    prompt_rendered = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    
    metadata_info = Column(JSONB, default=dict) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    trace = relationship("src.modules.sales_agent.infrastructure.models.agent_trace_model.AgentTrace", back_populates="llm_logs")
