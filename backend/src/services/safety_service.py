import re
import structlog
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from src.services.database import SessionLocal
from src.services.db.models.business import SensitiveData
from src.core.llm.providers.openai import OpenAIService
from langchain_core.messages import SystemMessage, HumanMessage

logger = structlog.get_logger()

class SafetyLayerService:
    """
    Orchestrates the detection and replacement of sensitive data using:
    1. Deterministic Regex/Keyword Matching (Fast, Rule-based)
    2. Contextual LLM Verification (Slow, Intelligent)
    """
    def __init__(self):
        self.llm_service = OpenAIService() # Adapter for OpenAI/LLM
        
    def _get_rules(self, db: Session) -> List[SensitiveData]:
        """Fetch active rules from DB."""
        return db.query(SensitiveData).filter(SensitiveData.is_active == True).all()

    async def sanitize_content(self, content: str) -> Tuple[str, bool]:
        """
        Main entry point. Returns (sanitized_content, was_modified).
        """
        if not content:
            return content, False
            
        modified_flag = False
        final_content = content
        
        db = SessionLocal()
        try:
            rules = self._get_rules(db)
            
            # --- PHASE 1: DETERMINISTIC (Regex) ---
            for rule in rules:
                try:
                    # Case insensitive search
                    # Note: We assume 'pattern' is a valid regex or simple string
                    # If simple string, escape it. If user intends regex, they should provide valid regex.
                    # For MVP, we treat it as regex.
                    
                    matches = re.finditer(rule.pattern, final_content, re.IGNORECASE)
                    
                    for match in matches:
                        match_text = match.group(0)
                        
                        # If context_instruction exists, use LLM to verify
                        if rule.context_instruction:
                            should_replace = await self._verify_context(match_text, final_content, rule.context_instruction)
                            if not should_replace:
                                continue
                        
                        # Replace
                        final_content = final_content.replace(match_text, rule.replacement)
                        modified_flag = True
                        logger.info("safety_layer_trigger", rule_id=str(rule.id), category=rule.category)
                        
                except re.error as e:
                    logger.error(f"Invalid regex pattern for rule {rule.id}: {e}")
                    continue

            # --- PHASE 2: SYSTEM GUARDRAILS (Hardcoded criticals) ---
            # Fallback for credit cards if not in DB
            # Simple Luhn-like or broad pattern
            cc_pattern = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
            if re.search(cc_pattern, final_content):
                final_content = re.sub(cc_pattern, "[REDACTED_PAYMENT_INFO]", final_content)
                modified_flag = True
                logger.warning("safety_layer_trigger_system", type="credit_card")

            return final_content, modified_flag

        finally:
            db.close()

    async def _verify_context(self, match_text: str, full_context: str, instruction: str) -> bool:
        """
        Uses LLM (Fast Model) to verify if the match actually violates the rule in this specific context.
        Returns True if it SHOULD be replaced.
        """
        try:
            prompt = (
                f"Analiza el siguiente texto y determina si el fragmento '{match_text}' debe ser censurado/reemplazado.\n"
                f"Instrucción de Seguridad: {instruction}\n"
                f"Texto Completo: \"{full_context}\"\n\n"
                f"Responde SOLO con 'YES' si debe censurarse, o 'NO' si es seguro/falso positivo."
            )
            
            # Use fast model (gpt-3.5/flash)
            response = self.llm_service.generate_response(
                messages=[{"role": "user", "content": prompt}], 
                model_type="fast",
                temperature=0
            )
            
            return "YES" in response.strip().upper()
            
        except Exception as e:
            logger.error(f"Safety Layer LLM Check Failed: {e}")
            # Fail safe: If LLM fails, assume it IS sensitive to be safe (Paranoid Mode)
            return True
