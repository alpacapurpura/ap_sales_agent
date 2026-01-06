from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.core.llm.base import BaseLLMService
from src.config import settings

class OpenAIService(BaseLLMService):
    """
    Concrete implementation for OpenAI (Adapter Pattern).
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL
        self.embedding_model_name = settings.OPENAI_EMBEDDING_MODEL
        
        # Initialize LangChain Chat Model
        self.chat_model = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            temperature=0.7
        )
        
        # Initialize Embeddings Model
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model_name,
            openai_api_key=self.api_key
        )

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Adapts the generic message format to LangChain's format and invokes the model.
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
                # Handle case where system prompt is in the messages list
                lc_messages.append(SystemMessage(content=content))
                
        response = self.chat_model.invoke(lc_messages, **kwargs)
        return response.content

    def get_embedding_model(self) -> Any:
        return self.embeddings
        
    def get_client(self) -> Any:
        return self.chat_model
