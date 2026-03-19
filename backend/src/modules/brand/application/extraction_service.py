from typing import Optional, Literal
from uuid import UUID
from sqlalchemy.orm import Session
import structlog
import json
import asyncio
import time

from src.modules.brand.domain import (
    BrandSettings, BrandIdentity, BrandStory, BrandStrategy, BrandVisuals, BrandTeamWrapper
)
from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
from src.modules.copilot.infrastructure.prompts.brand_extraction.identity import BRAND_IDENTITY_PROMPT
from src.modules.copilot.infrastructure.prompts.brand_extraction.story import BRAND_STORY_PROMPT
from src.modules.copilot.infrastructure.prompts.brand_extraction.team import BRAND_TEAM_PROMPT
from src.modules.copilot.infrastructure.prompts.brand_extraction.strategy import BRAND_STRATEGY_PROMPT
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from src.modules.copilot.application.services.web_extractor_adapter import extract_from_url
from src.shared.application.ai_action_service import AIActionService, AIActionPolicy, AIModelPolicy

logger = structlog.get_logger()

class BrandExtractionService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = BrandRepository(db)
        self.ai_action_service = AIActionService()
        self.default_policy = AIActionPolicy(
            retries=2,
            retry_delay_seconds=0.4,
            model=AIModelPolicy(
                model_type="smart",
                temperature=0,
                max_output_tokens=1800,
            ),
        )

    async def crawl_content(self, url: str) -> str:
        """
        Crawls the URL and up to 5 internal subpages, returning aggregated text content
        using httpx + BeautifulSoup.
        """
        try:
            base_domain = urlparse(url).netloc
            all_text_parts: list[str] = []
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                # Fetch main page
                response = await client.get(url)
                response.raise_for_status()
                main_text = self._extract_text_from_html(response.text)
                all_text_parts.append(main_text)

                # Depth 1: find internal links from main page
                soup = BeautifulSoup(response.text, "html.parser")
                seen_urls: set[str] = {url}
                internal_links: list[str] = []

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)
                    # Same domain, not already seen, HTTP(S) only
                    if (
                        parsed.netloc == base_domain
                        and full_url not in seen_urls
                        and parsed.scheme in ("http", "https")
                    ):
                        seen_urls.add(full_url)
                        internal_links.append(full_url)
                        if len(internal_links) >= 5:
                            break

                # Fetch subpages
                for link in internal_links:
                    try:
                        sub_response = await client.get(link)
                        sub_response.raise_for_status()
                        sub_text = self._extract_text_from_html(sub_response.text)
                        if sub_text.strip():
                            all_text_parts.append(sub_text)
                    except Exception:
                        continue

            result = "\n\n".join(all_text_parts)[:100_000]
            pages_crawled = 1 + len([p for p in all_text_parts[1:] if p.strip()])
            logger.info("crawl_completed", url=url, pages_crawled=pages_crawled, total_chars=len(result))
            return result

        except Exception as e:
            logger.error("crawl_exception", url=url, error=str(e))
            return ""

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Parse HTML and extract clean text content, removing non-content elements."""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    async def extract_all(
        self, 
        url: Optional[str] = None, 
        text: Optional[str] = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: Optional[str] = None,
        dry_run: bool = False,
        include_visuals: bool = False
    ) -> BrandSettings:
        """
        Orchestrates the full brand extraction process.
        """
        # 1. Get Content
        content = text or ""
        extracted_visuals = None

        if url:
            logger.info("starting_crawl", url=url)
            
            # Parallel Execution: Crawl + Visuals
            t0 = time.time()
            
            async def safe_crawl():
                try:
                    return await self.crawl_content(url)
                except Exception as e:
                    logger.error("crawl_failed", error=str(e))
                    return ""

            async def safe_visuals():
                if not include_visuals:
                    return None
                try:
                    # Extended timeout to allow both processes to complete
                    return await asyncio.wait_for(extract_from_url(url, BrandVisuals), timeout=120.0)
                except asyncio.TimeoutError:
                    logger.error("visual_extraction_timeout", url=url)
                    return None
                except Exception as e:
                    logger.error("visual_extraction_failed", error=str(e))
                    return None

            # Execute both concurrently
            crawled_content, extracted_visuals = await asyncio.gather(safe_crawl(), safe_visuals())
            
            t1 = time.time()
            logger.info("parallel_extraction_completed", 
                        duration=t1-t0, 
                        crawl_length=len(crawled_content), 
                        visuals_success=bool(extracted_visuals)
            )

            if crawled_content:
                content = f"{content}\n\n{crawled_content}"
        
        # In 'update' mode, we proceed even if content is minimal, as instructions might be enough?
        # But generally we need some content or instructions.
        if not content.strip() and not update_instructions:
            logger.warning("no_content_to_extract", tenant_id=self.tenant_id)
            return self.repository.get_settings(self.tenant_id)

        logger.info("extraction_context_prepared", total_content_length=len(content))

        # 2. Prepare Context (Current Data)
        current_settings = self.repository.get_settings(self.tenant_id)
        current_data_str = ""
        if mode == "update":
            current_data_str = json.dumps(current_settings.model_dump(mode='json'), indent=2)

        # 3. Debug Logging
        logger.info("extraction_content_ready", 
                    content_length=len(content),
                    current_data_length=len(current_data_str)
        )

        # 3. Run Extractions concurrently (each uses asyncio.to_thread internally)
        logger.info("starting_llm_extractions", sections=4, concurrent=True)

        identity, story, strategy, team_wrapper = await asyncio.gather(
            self._extract_identity(content, current_data_str, update_instructions),
            self._extract_story(content, current_data_str, update_instructions),
            self._extract_strategy(content, current_data_str, update_instructions),
            self._extract_team(content, current_data_str, update_instructions),
        )
        
        # 4. Merge & Save
        return self._merge_and_save(identity, story, strategy, team_wrapper, extracted_visuals, dry_run=dry_run)

    async def _extract_identity(self, content: str, current_data: str, instructions: str) -> BrandIdentity:
        try:
            prompt = BRAND_IDENTITY_PROMPT.format(
                content=content[:50000], 
                visual_context="",
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            return await asyncio.to_thread(
                self.ai_action_service.run_structured_action,
                action_name="brand_extract_identity",
                tenant_id=self.tenant_id,
                system_prompt=self._append_schema_instruction(prompt, BrandIdentity),
                user_prompt="Extract the Brand Identity.",
                response_model=BrandIdentity,
                policy=self.default_policy,
                metadata={"prompt_template": "brand_identity_extraction"},
            )
        except Exception as e:
            logger.error("extract_identity_failed", error=str(e))
            return BrandIdentity()

    async def _extract_story(self, content: str, current_data: str, instructions: str) -> BrandStory:
        try:
            prompt = BRAND_STORY_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            return await asyncio.to_thread(
                self.ai_action_service.run_structured_action,
                action_name="brand_extract_story",
                tenant_id=self.tenant_id,
                system_prompt=self._append_schema_instruction(prompt, BrandStory),
                user_prompt="Extract the Brand Story.",
                response_model=BrandStory,
                policy=self.default_policy,
                metadata={"prompt_template": "brand_story_extraction"},
            )
        except Exception as e:
            logger.error("extract_story_failed", error=str(e))
            return BrandStory()

    async def _extract_strategy(self, content: str, current_data: str, instructions: str) -> BrandStrategy:
        try:
            prompt = BRAND_STRATEGY_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            return await asyncio.to_thread(
                self.ai_action_service.run_structured_action,
                action_name="brand_extract_strategy",
                tenant_id=self.tenant_id,
                system_prompt=self._append_schema_instruction(prompt, BrandStrategy),
                user_prompt="Extract the Brand Strategy.",
                response_model=BrandStrategy,
                policy=self.default_policy,
                metadata={"prompt_template": "brand_strategy_extraction"},
            )
        except Exception as e:
            logger.error("extract_strategy_failed", error=str(e))
            return BrandStrategy()

    async def _extract_team(self, content: str, current_data: str, instructions: str) -> BrandTeamWrapper:
        try:
            prompt = BRAND_TEAM_PROMPT.format(
                content=content[:50000],
                current_data=current_data or "None",
                instructions=instructions or "None"
            )
            return await asyncio.to_thread(
                self.ai_action_service.run_structured_action,
                action_name="brand_extract_team",
                tenant_id=self.tenant_id,
                system_prompt=self._append_schema_instruction(prompt, BrandTeamWrapper),
                user_prompt="Extract the Team structure.",
                response_model=BrandTeamWrapper,
                policy=self.default_policy,
                metadata={"prompt_template": "brand_team_extraction"},
            )
        except Exception as e:
            logger.error("extract_team_failed", error=str(e))
            return BrandTeamWrapper()

    def _append_schema_instruction(self, prompt: str, schema_model) -> str:
        schema_json = json.dumps(schema_model.model_json_schema(), indent=2)
        return f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."

    def _merge_and_save(
        self, 
        new_identity: BrandIdentity, 
        new_story: BrandStory, 
        new_strategy: BrandStrategy,
        new_team_wrapper: BrandTeamWrapper,
        new_visuals: Optional[BrandVisuals] = None,
        dry_run: bool = False
    ) -> BrandSettings:
        
        current_settings = self.repository.get_settings(self.tenant_id)
        
        # Merge Identity (Update non-null fields)
        updated_identity = current_settings.identity.model_dump() if current_settings.identity else {}
        new_identity_dict = new_identity.model_dump(exclude_unset=True, exclude_none=True)
        updated_identity.update(new_identity_dict)
        
        # Merge Story
        updated_story = current_settings.story.model_dump() if current_settings.story else {}
        new_story_dict = new_story.model_dump(exclude_unset=True, exclude_none=True)
        if "milestones" in new_story_dict and new_story_dict["milestones"]:
            updated_story["milestones"] = new_story_dict["milestones"]
            del new_story_dict["milestones"]
        updated_story.update(new_story_dict)

        # Merge Strategy
        updated_strategy = current_settings.strategy.model_dump() if current_settings.strategy else {}
        new_strategy_dict = new_strategy.model_dump(exclude_unset=True, exclude_none=True)
        if "competitors" in new_strategy_dict and new_strategy_dict["competitors"]:
            updated_strategy["competitors"] = new_strategy_dict["competitors"]
            del new_strategy_dict["competitors"]
        updated_strategy.update(new_strategy_dict)

        # Merge Team
        updated_team = current_settings.team
        if new_team_wrapper.key_leadership:
            updated_team = new_team_wrapper.key_leadership
            
        # Merge Visuals
        updated_visuals = current_settings.visuals.model_dump() if current_settings.visuals else {}
        if new_visuals:
            new_visuals_dict = new_visuals.model_dump(exclude_unset=True, exclude_none=True)
            updated_visuals.update(new_visuals_dict)
        
        # Construct new Settings
        final_settings = current_settings.model_copy(update={
            "identity": BrandIdentity(**updated_identity),
            "story": BrandStory(**updated_story),
            "strategy": BrandStrategy(**updated_strategy),
            "team": updated_team,
            "visuals": BrandVisuals(**updated_visuals)
        })
        
        if dry_run:
            logger.info("dry_run_extraction_completed", tenant_id=self.tenant_id)
            # LOGGING FOR DEBUGGING
            print("\n--- [DEBUG] LLM EXTRACTION RESULT (Dry Run) ---")
            print(json.dumps(final_settings.model_dump(mode='json'), indent=2))
            print("-------------------------------------------------\n")
            return final_settings

        return self.repository.save_settings(self.tenant_id, final_settings)
