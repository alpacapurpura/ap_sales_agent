from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    
    # Channel specific IDs
    telegram_id = Column(String, unique=True, nullable=True)
    whatsapp_id = Column(String, unique=True, nullable=True)
    instagram_id = Column(String, unique=True, nullable=True)
    tiktok_id = Column(String, unique=True, nullable=True)
    
    # Profile Data (The "Valeria" Profile)
    # Stores the full UserProfile schema (psychographics + demographics + qualification)
    profile_data = Column(JSONB, default={}) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    messages = relationship("Message", back_populates="user")

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # program, webinar, community
    status = Column(String, default="active") # active, archived
    
    # Pricing Configuration
    # {"regular": 5925, "offer": 4444, "currency": "PEN"}
    pricing = Column(JSONB, default={})
    
    # Date Configuration
    # {"start": "2026-02-10", "offer_deadline": "2026-08-12"}
    dates = Column(JSONB, default={})
    
    # Content/Metadata
    metadata_info = Column(JSONB, default={})
    
    # Downsell Strategy
    downsell_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    # Relationships
    downsell_product = relationship("Product", remote_side=[id])
    enrollments = relationship("Enrollment", back_populates="product")

class Enrollment(Base):
    """
    Tracks the User's journey with a specific Product.
    """
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    # Status in the funnel
    # awareness, qualified, objection_handling, call_booked, enrolled, downsell_accepted, disqualified
    status = Column(String, default="awareness")
    
    # Funnel Stage
    stage = Column(String, default="awareness")
    
    # 0-100 score based on profile match and intent
    lead_score = Column(Integer, default=0)
    
    # Objections raised
    # ["price", "time", "spousal_approval"]
    objections = Column(JSONB, default=[])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="enrollments")
    product = relationship("Product", back_populates="enrollments")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled") # scheduled, completed, no_show, cancelled
    meeting_link = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="appointments")

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

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    category = Column(String, default="general") # factural, style, objection, general
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="indexed") # indexed, error
    
    # Metadata extra (e.g. description, author)
    metadata_info = Column(JSONB, default={})

class OfferLog(Base):
    """
    Tracks specific pitch events (When was a product offered?)
    """
    __tablename__ = "offer_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    offered_at = Column(DateTime(timezone=True), server_default=func.now())
    pitch_type = Column(String) # e.g., "webinar_invite", "program_pitch", "downsell"
    response = Column(String, default="pending") # pending, accepted, rejected, ignored
    
    user = relationship("User")
    product = relationship("Product")

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

class PromptVersion(Base):
    """
    Manages versions of Prompt Templates.
    Enables runtime updates and audit trail for prompts.
    """
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, index=True) # e.g., "sales_system"
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False) # Jinja2 template content
    is_active = Column(Boolean, default=False)
    
    change_reason = Column(String, nullable=False) # Mandatory audit field
    author_id = Column(String, default="admin") # User who made the change
    
    # Metadata for intelligence & management
    # { 
    #   "target_node": "manager", 
    #   "target_model": "gpt-4", 
    #   "input_variables": ["user_profile"],
    #   "description": "Main system prompt for sales"
    # }
    metadata_info = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
