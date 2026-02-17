from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import structlog
import json

from src.services.db.models.tenant import Tenant
from src.core.domain.brand_schema import BrandSettings, BrandIdentity, BrandStory, KeyFigure, BrandStrategy
from src.core.prompts.brand_extraction.identity import BRAND_IDENTITY_PROMPT
from src.core.prompts.brand_extraction.story import BRAND_STORY_PROMPT
from src.core.prompts.brand_extraction.team import BRAND_TEAM_PROMPT
from src.core.prompts.brand_extraction.strategy import BRAND_STRATEGY_PROMPT
from src.core.agents.web_extractor.graph import web_extractor_graph

logger = structlog.get_logger()

# Schema local para la extracción de equipo, ya que el prompt devuelve más info que solo la lista
class BrandTeamWrapper(BaseModel):
    key_leadership: List[KeyFigure] = Field(default_factory=list, description="Personas clave identificadas")
    culture_vibe: Optional[str] = Field(None, description="Descripción de la cultura")
    locations: Optional[str] = Field(None, description="Ubicaciones operativas")

class BrandExtractionService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        # Use gpt-4o for better reasoning and extraction quality on complex tasks
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    async def crawl_content(self, url: str) -> str:
        """
        Crawls the URL and returns aggregated text content using the Web Extractor Graph in 'crawl_only' mode.
        """
        initial_state = {
            "base_url": url,
            "queue": [url],
            "visited": [],
            "depth": 0,
            "max_depth": 1, # Crawl 1 level deep for better context
            "mode": "crawl_only",
            "aggregated_content": [],
            "target_schema": {}, # Dummy schema
            "retry_count": 0,
            "error": None
        }
        
        try:
            result = await web_extractor_graph.ainvoke(initial_state)
            if result.get("error"):
                logger.error("crawl_failed", url=url, error=result["error"])
                return ""
            
            extracted = result.get("extracted_data", {})
            return extracted.get("content", "")
        except Exception as e:
            logger.error("crawl_exception", url=url, error=str(e))
            return ""

    async def extract_all(
        self, 
        url: Optional[str] = None, 
        text: Optional[str] = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: Optional[str] = None,
        dry_run: bool = False
    ) -> BrandSettings:
        """
        Orchestrates the full brand extraction process.
        """
        # 1. Get Content
        content = text or ""
        if url:
            logger.info("starting_crawl", url=url)
            crawled_content = await self.crawl_content(url)
            logger.info("crawl_completed", url=url, content_length=len(crawled_content))
            if crawled_content:
                content = f"{content}\n\n{crawled_content}"
        
        # In 'update' mode, we proceed even if content is minimal, as instructions might be enough?
        # But generally we need some content or instructions.
        if not content.strip() and not update_instructions:
            logger.warning("no_content_to_extract", tenant_id=self.tenant_id)
            return self._get_current_brand_settings()

        logger.info("extraction_context_prepared", total_content_length=len(content))

        # 2. Prepare Context (Current Data)
        current_settings = self._get_current_brand_settings()
        current_data_str = ""
        if mode == "update":
            current_data_str = json.dumps(current_settings.model_dump(mode='json'), indent=2)

        # 3. Debug Logging
        logger.info("extraction_content_ready", 
                    content_length=len(content),
                    current_data_length=len(current_data_str)
        )

        # 3. Run Extractions
        # We pass current_data and instructions to prompts
        
        identity = await self._extract_identity(content, current_data_str, update_instructions)
        story = await self._extract_story(content, current_data_str, update_instructions)
        strategy = await self._extract_strategy(content, current_data_str, update_instructions)
        team_wrapper = await self._extract_team(content, current_data_str, update_instructions)
        
        # 4. Merge & Save
        return self._merge_and_save(identity, story, strategy, team_wrapper, dry_run=dry_run)

    async def _extract_identity(self, content: str, current_data: str, instructions: str) -> BrandIdentity:
        try:
            # Use json_mode for better compliance with complex schemas where optional fields are ignored by function calling
            structured_llm = self.llm.with_structured_output(BrandIdentity, method="json_mode")
            
            schema_json = json.dumps(BrandIdentity.model_json_schema(), indent=2)
            
            prompt = BRAND_IDENTITY_PROMPT.format(
                content=content[:50000], 
                visual_context="",
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            
            # Append schema instruction
            system_prompt = f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Extract the Brand Identity.")
            ]
            result = await structured_llm.ainvoke(messages)
            logger.info("extraction_raw_result", type="identity", result=result)
            if isinstance(result, dict):
                return BrandIdentity(**result)
            return result
        except Exception as e:
            logger.error("extract_identity_failed", error=str(e))
            return BrandIdentity()

    async def _extract_story(self, content: str, current_data: str, instructions: str) -> BrandStory:
        try:
            structured_llm = self.llm.with_structured_output(BrandStory, method="json_mode")
            schema_json = json.dumps(BrandStory.model_json_schema(), indent=2)
            
            prompt = BRAND_STORY_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            
            system_prompt = f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Extract the Brand Story.")
            ]
            result = await structured_llm.ainvoke(messages)
            logger.info("extraction_raw_result", type="story", result=result)
            if isinstance(result, dict):
                return BrandStory(**result)
            return result
        except Exception as e:
            logger.error("extract_story_failed", error=str(e))
            return BrandStory()

    async def _extract_strategy(self, content: str, current_data: str, instructions: str) -> BrandStrategy:
        try:
            structured_llm = self.llm.with_structured_output(BrandStrategy, method="json_mode")
            schema_json = json.dumps(BrandStrategy.model_json_schema(), indent=2)
            
            prompt = BRAND_STRATEGY_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            
            system_prompt = f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Extract the Brand Strategy.")
            ]
            result = await structured_llm.ainvoke(messages)
            logger.info("extraction_raw_result", type="strategy", result=result)
            if isinstance(result, dict):
                return BrandStrategy(**result)
            return result
        except Exception as e:
            logger.error("extract_strategy_failed", error=str(e))
            return BrandStrategy()

    async def _extract_team(self, content: str, current_data: str, instructions: str) -> BrandTeamWrapper:
        try:
            structured_llm = self.llm.with_structured_output(BrandTeamWrapper, method="json_mode")
            schema_json = json.dumps(BrandTeamWrapper.model_json_schema(), indent=2)
            
            prompt = BRAND_TEAM_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            
            system_prompt = f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Extract the Team structure.")
            ]
            result = await structured_llm.ainvoke(messages)
            logger.info("extraction_raw_result", type="team", result=result)
            if isinstance(result, dict):
                return BrandTeamWrapper(**result)
            return result
        except Exception as e:
            logger.error("extract_team_failed", error=str(e))
            return BrandTeamWrapper()

    def _get_current_brand_settings(self) -> BrandSettings:
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            return BrandSettings()
        
        config = tenant.config_json or {}
        return BrandSettings(**config.get("brand_settings", {}))

    def _merge_and_save(
        self, 
        new_identity: BrandIdentity, 
        new_story: BrandStory, 
        new_strategy: BrandStrategy,
        new_team_wrapper: BrandTeamWrapper,
        dry_run: bool = False
    ) -> BrandSettings:
        from sqlalchemy.orm.attributes import flag_modified
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")
            
        # Ensure config is a dict and make a deep copy to trigger SQLAlchemy detection
        config = dict(tenant.config_json or {})
        current_brand_data = config.get("brand_settings", {})
        
        # Initialize defaults if empty
        if not current_brand_data:
            current_brand_data = BrandSettings().model_dump(mode='json')
            
        current_settings = BrandSettings(**current_brand_data)
        
        # Merge Identity (Update non-null fields)
        updated_identity = current_settings.identity.model_dump()
        new_identity_dict = new_identity.model_dump(exclude_unset=True, exclude_none=True)
        updated_identity.update(new_identity_dict)
        
        # Merge Story
        updated_story = current_settings.story.model_dump()
        new_story_dict = new_story.model_dump(exclude_unset=True, exclude_none=True)
        if "milestones" in new_story_dict and new_story_dict["milestones"]:
            updated_story["milestones"] = new_story_dict["milestones"]
            del new_story_dict["milestones"]
        updated_story.update(new_story_dict)

        # Merge Strategy
        updated_strategy = current_settings.strategy.model_dump()
        new_strategy_dict = new_strategy.model_dump(exclude_unset=True, exclude_none=True)
        if "competitors" in new_strategy_dict and new_strategy_dict["competitors"]:
            updated_strategy["competitors"] = new_strategy_dict["competitors"]
            del new_strategy_dict["competitors"]
        updated_strategy.update(new_strategy_dict)

        # Merge Team
        updated_team = current_settings.team
        if new_team_wrapper.key_leadership:
            updated_team = new_team_wrapper.key_leadership
        
        # Construct new Settings
        final_settings = current_settings.model_copy(update={
            "identity": BrandIdentity(**updated_identity),
            "story": BrandStory(**updated_story),
            "strategy": BrandStrategy(**updated_strategy),
            "team": updated_team
        })
        
        if dry_run:
            logger.info("dry_run_extraction_completed", tenant_id=self.tenant_id)
            # LOGGING FOR DEBUGGING
            print("\n--- [DEBUG] LLM EXTRACTION RESULT (Dry Run) ---")
            print(json.dumps(final_settings.model_dump(mode='json'), indent=2))
            print("-------------------------------------------------\n")
            return final_settings

        # Save to DB - EXPLICITLY REASSIGN THE DICT TO TRIGGER CHANGE TRACKING
        config["brand_settings"] = final_settings.model_dump(mode='json')
        
        # Important: SQLAlchemy JSON fields sometimes don't detect in-place mutations
        # Re-assigning the whole dictionary ensures the flag_modified behavior
        tenant.config_json = config
        
        # Explicitly flag modification for JSON field
        flag_modified(tenant, "config_json")
        
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        
        return final_settings
