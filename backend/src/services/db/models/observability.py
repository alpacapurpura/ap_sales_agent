from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    role = Column(String, nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    channel = Column(String, nullable=True) # telegram, whatsapp
    
    # Context
    product_context_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    # Cognitive Traceability
    # { "thought": "...", "intent": "...", "state_snapshot": "S3_Gap" }
    metadata_log = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")

class AgentTrace(Base):
    """
    Logs the execution flow of the Agent (Node by Node).
    Equivalent to a "Span" in observability.
    """
    __tablename__ = "agent_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=True) # To group a single turn
    
    node_name = Column(String, nullable=False) # e.g. "manager", "router"
    input_state = Column(JSONB, default={}) # Snapshot of state BEFORE execution
    output_state = Column(JSONB, default={}) # Snapshot of state AFTER execution
    
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to LLM Logs
    llm_logs = relationship("LLMCallLog", back_populates="trace")

class LLMCallLog(Base):
    """
    Logs specific LLM calls made during a node execution.
    """
    __tablename__ = "llm_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("agent_traces.id"), nullable=True)
    
    model = Column(String) # e.g. "gpt-4-turbo"
    prompt_template = Column(String, nullable=True) # Name of template used
    prompt_rendered = Column(Text) # The actual full text sent to LLM
    response_text = Column(Text) # The raw output
    
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    
    # Metadata for advanced debugging (e.g. RAG chunks, tool calls)
    metadata_info = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    trace = relationship("AgentTrace", back_populates="llm_logs")
