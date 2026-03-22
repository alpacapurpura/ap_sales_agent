from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.shared.infrastructure.llm.base import BaseLLMService
from src.core.config import settings


class GeminiService(BaseLLMService):
    """
    Concrete implementation for Google Gemini (Adapter Pattern).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        # Gemini embedding model usually is "models/embedding-001"
        self.embedding_model_name = "models/embedding-001" 
        
        if not self.api_key:
            # Only raise if strictly required and not provided
            # raise ValueError("GEMINI_API_KEY is not set in configuration.")
            pass
            
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
            
            # Usage metadata available but logging removed to decouple shared from sales_agent
            
        except Exception as e:
            response_text = f"ERROR: {str(e)}"
            raise e
        
        # Logging logic removed to decouple shared from sales_agent.

        return response_text

    def get_embedding_model(self) -> Any:
        return self.embeddings
        
    def get_client(self) -> Any:
        return self.chat_model
