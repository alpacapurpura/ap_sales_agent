from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.core.llm.base import BaseLLMService
from src.config import settings

from src.core.tracing import current_trace_id
from src.services.db.repositories.audit import AuditRepository
from src.services.database import SessionLocal

class GeminiService(BaseLLMService):
    """
    Concrete implementation for Google Gemini (Adapter Pattern).
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        # Gemini embedding model usually is "models/embedding-001"
        self.embedding_model_name = "models/embedding-001" 
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in configuration.")
            
        # Initialize LangChain Chat Model
        self.chat_model = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True # Gemini sometimes prefers this
        )
        
        # Initialize Embeddings Model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model_name,
            google_api_key=self.api_key
        )

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Adapts the generic message format to LangChain's format for Gemini.
        """
        lc_messages = []
        
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
            
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
                
        try:
            response = self.chat_model.invoke(lc_messages, **kwargs)
            response_text = response.content
            
            # Extract Usage Metadata
            # Google Generative AI usually provides usage_metadata
            usage = response.usage_metadata or {}
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)
            
        except Exception as e:
            response_text = f"ERROR: {str(e)}"
            tokens_in = 0
            tokens_out = 0
            raise e
        finally:
            # --- TRACING LOGIC ---
            trace_id = current_trace_id.get()
            if trace_id:
                try:
                    db = SessionLocal()
                    repo = AuditRepository(db)
                    full_prompt_str = f"System: {system_prompt}\nMessages: {messages}"
                    
                    repo.create_llm_log(
                        trace_id=trace_id,
                        model=self.model_name,
                        prompt_template="unknown",
                        prompt_rendered=full_prompt_str,
                        response_text=response_text,
                        tokens_input=tokens_in,
                        tokens_output=tokens_out
                    )
                    repo.close()
                except Exception as log_err:
                    print(f"Failed to log Gemini LLM call: {log_err}")
                    
        return response_text

    def get_embedding_model(self) -> Any:
        return self.embeddings
        
    def get_client(self) -> Any:
        return self.chat_model
