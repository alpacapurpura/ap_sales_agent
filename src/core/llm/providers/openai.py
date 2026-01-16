from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.core.llm.base import BaseLLMService
from src.config import settings

from src.core.tracing import current_trace_id
from src.services.repository import Repository

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
        
        # Initialize Fast Model (for tiered compute)
        self.fast_chat_model = ChatOpenAI(
            model=settings.OPENAI_FAST_MODEL,
            openai_api_key=self.api_key,
            temperature=0.7
        )
        
        # Initialize Embeddings Model
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model_name,
            openai_api_key=self.api_key
        )

    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, model_type: str = "smart", **kwargs) -> str:
        """
        Adapts the generic message format to LangChain's format and invokes the model.
        Args:
            model_type: "smart" (GPT-4) or "fast" (GPT-3.5/Mini)
        """
        # Init vars for logging in finally block
        response_text = ""
        tokens_in = 0
        tokens_out = 0
        selected_model = None
        meta_log = {}

        try:
            # --- ROBUSTNESS CHECK ---
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]

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
            
            # Select Model based on Tier
            selected_model = self.fast_chat_model if model_type == "fast" else self.chat_model
            
            # --- PARAMETER OVERRIDE ---
            # Allow overriding generation parameters per call
            # Note: LangChain 'invoke' might not accept all params directly as kwargs depending on version/method.
            # For ChatOpenAI, we usually pass them to the constructor OR bind them.
            # But 'invoke' often propagates extra args to the underlying API call (e.g. temperature, max_tokens).
            
            # Explicitly extract known OpenAI params
            # temperature, max_tokens, top_p, presence_penalty, frequency_penalty
            
            call_params = {}
            if "temperature" in kwargs: call_params["temperature"] = kwargs.pop("temperature")
            if "max_tokens" in kwargs: call_params["max_tokens"] = kwargs.pop("max_tokens")
            if "max_output_tokens" in kwargs: call_params["max_tokens"] = kwargs.pop("max_output_tokens") # Alias
            if "top_p" in kwargs: call_params["top_p"] = kwargs.pop("top_p")
            if "presence_penalty" in kwargs: call_params["presence_penalty"] = kwargs.pop("presence_penalty")
            if "frequency_penalty" in kwargs: call_params["frequency_penalty"] = kwargs.pop("frequency_penalty")
            
            # Extract metadata passed in kwargs (e.g. RAG context) BEFORE invoke
            # to avoid collision with LangChain internals
            if "metadata" in kwargs:
                meta_log = kwargs.pop("metadata")

            # If we have params, we might need to bind them or pass to invoke.
            # LangChain's invoke(..., **kwargs) usually passes extra params to the model run.
            # Let's merge them back into kwargs for invoke.
            kwargs.update(call_params)

            # --- LLM CALL ---
            response = selected_model.invoke(lc_messages, **kwargs)
            response_text = response.content
            
            # Extract Usage Metadata
            usage = response.response_metadata.get("token_usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)
            
        except Exception as e:
            # We still want to log the error if possible
            response_text = f"ERROR: {str(e)}"
            raise e
        finally:
            # --- TRACING LOGIC ---
            trace_id = current_trace_id.get()
            if trace_id:
                try:
                    repo = Repository()
                    # Reconstruct prompt for logging
                    full_prompt_str = f"System: {system_prompt}\nMessages: {messages}"
                    
                    # Ensure model name is captured even if selection failed
                    model_name = selected_model.model_name if selected_model else "unknown"
                    
                    # Extract metadata passed in kwargs (e.g. RAG context)
                    meta_log = kwargs.get("metadata", {})

                    repo.create_llm_log(
                        trace_id=trace_id,
                        model=model_name,
                        prompt_template="unknown", # We'd need to pass this arg to support it
                        prompt_rendered=full_prompt_str,
                        response_text=response_text,
                        tokens_input=tokens_in, 
                        tokens_output=tokens_out,
                        metadata=meta_log
                    )
                    repo.close()
                except Exception as log_err:
                    print(f"Failed to log LLM call: {log_err}")

        return response_text

    def get_embedding_model(self) -> Any:
        return self.embeddings
        
    def get_client(self) -> Any:
        return self.chat_model
