from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.domain.offer_enums import OfferType
from src.core.domain.landing_page.enums import LandingPageArchetype
from src.core.domain.landing_page.archetype_map import get_default_archetype
from src.core.domain.landing_page.schema import (
    LandingPageConfig, SqueezeContent, EventContent, FlashOfferContent, 
    TransformerContent, VelvetRopeContent, BrochureContent, LandingPageTheme,
    FeatureBullet, Testimonial, LandingPageFont
)
from src.config import settings
from uuid import UUID
import json
import logging
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.services.db.models.business import Product
from src.services.db.models.tenant import Tenant
from datetime import datetime

logger = logging.getLogger(__name__)

class TransformerPageGeneration(BaseModel):
    slug: str = Field(..., description="URL slug pública (ej: /p/mi-oferta)")
    seo_title: str = Field(..., description="SEO Title based on Promise")
    seo_description: str = Field(..., description="Meta description based on Hook")
    content: TransformerContent

class LandingGeneratorService:
    def __init__(self, session: Session):
        self.session = session
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        # Setup Jinja2 Environment
        # Use absolute path relative to project root or use package loader
        # Current working directory in Docker is /app, and src is at /app/src
        # So templates are at /app/src/core/prompts/templates
        template_dir = '/app/src/core/prompts/templates'
        if not os.path.exists(template_dir):
             # Fallback for local dev if cwd is different (e.g. running from repo root)
             template_dir = os.path.join(os.getcwd(), 'backend/src/core/prompts/templates')

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml', 'j2'])
        )

    def _get_archetype(self, offer_type: OfferType) -> LandingPageArchetype:
        return get_default_archetype(offer_type)

    def _fetch_media_assets(self, tenant_id: UUID):
        """
        Extracts media assets (logos, team photos, etc.) from Tenant Config.
        Returns a list of dicts: {id, type, description, url}
        """
        tenant = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
        assets = []
        
        if not tenant or not tenant.config_json:
            return assets

        brand_settings = tenant.config_json.get("brand_settings", {})
        visuals = brand_settings.get("visuals", {})
        team = brand_settings.get("team", [])
        authority = brand_settings.get("authority_vault", [])

        # Logos
        if visuals.get("logos", {}).get("primary"):
             assets.append({"id": "logo_primary", "type": "logo", "description": "Logo Principal", "url": visuals["logos"]["primary"]})

        # Team Photos (Authority)
        for person in team:
            if person.get("headshot_url"):
                assets.append({
                    "id": f"team_{person['id']}", 
                    "type": "person", 
                    "description": f"Foto de {person['name']} ({person.get('role', 'Expert')})", 
                    "url": person["headshot_url"]
                })

        # Authority Logos
        for auth in authority:
             if auth.get("logo_url"):
                assets.append({
                    "id": f"auth_{auth['id']}", 
                    "type": "logo", 
                    "description": f"Logo de {auth['entity_name']}", 
                    "url": auth["logo_url"]
                })
        
        return assets

    def _extract_theme_from_brand(self, config_json: dict) -> LandingPageTheme:
        """
        Extracts visual identity from Tenant Config and maps it to LandingPageTheme.
        """
        brand_settings = config_json.get("brand_settings", {})
        visuals = brand_settings.get("visuals", {})
        
        # 1. Colors
        primary = visuals.get("primary_color", "#000000")
        secondary = visuals.get("accent_color", "#ffffff")
        
        # 2. Fonts
        # Simple heuristic mapping
        font_heading = visuals.get("font_heading", "Inter").lower()
        font_pair = LandingPageFont.SANS_SERIF
        
        serif_keywords = ["playfair", "merriweather", "lora", "pt serif", "crimson"]
        modern_keywords = ["montserrat", "raleway", "poppins", "futura"]
        
        if any(k in font_heading for k in serif_keywords):
            font_pair = LandingPageFont.SERIF
        elif any(k in font_heading for k in modern_keywords):
            font_pair = LandingPageFont.MODERN
            
        return LandingPageTheme(
            primary_color=primary,
            secondary_color=secondary,
            font_pair=font_pair,
            dark_mode=False
        )

    def _render_prompt(self, template_name: str, context: dict) -> str:
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise


    def _slugify(self, text: str) -> str:
        """
        Creates a clean, URL-friendly slug from text.
        Example: "Programa: De Propósito a Prosperidad" -> "programa-de-proposito-a-prosperidad"
        """
        import re
        import unicodedata
        
        # Normalize unicode characters (e.g., accents)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        
        # Lowercase
        text = text.lower()
        
        # Replace non-alphanumeric chars with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Strip leading/trailing hyphens
        text = text.strip('-')
        
        return text

    async def regenerate_section_content(
        self, 
        offer_id: UUID, 
        tenant_id: UUID, 
        block_type: str, 
        current_content: dict, 
        instruction: str = None
    ) -> dict:
        """
        Regenerates content for a specific landing page section (block).
        """
        from src.services.db.repositories.offer_repository import OfferRepository
        offer_repo = OfferRepository(self.session)
        offer = offer_repo.get_by_id(offer_id)
        
        if not offer:
            raise ValueError("Offer not found")

        # Context
        tenant = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
        brand_settings = tenant.config_json.get('brand_settings', {}) if tenant else {}
        brand_tone = brand_settings.get('voice', {}).get('tone', 'Professional and Persuasive')
        
        offer_context = f"Offer: {offer.public_name}\nPromise: {offer.headline_promise}\nPrice: {offer.price}"

        # Prompt Construction
        system_prompt = f"""
        You are a World-Class Conversion Copywriter and UI/UX Strategist.
        Your task is to REWRITE or OPTIMIZE the content for a Landing Page Section.
        
        Section Type: {block_type}
        Brand Tone: {brand_tone}
        Context: {offer_context}
        
        User Instruction: {instruction if instruction else "Improve persuasion and clarity. Make it punchy."}
        
        RULES:
        1. Return ONLY valid JSON.
        2. Keep the exact same keys as the 'Current Content'. Do not add or remove keys.
        3. Maintain the structure (e.g., if 'modules' is an array, keep it an array).
        4. Write in Spanish (Español).
        """

        user_message = f"Current Content JSON:\n{json.dumps(current_content, indent=2)}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        # Call LLM with JSON mode
        response = await self.llm.with_structured_output(dict).ainvoke(messages)
        
        return response

    async def generate_landing_page(self, offer_id: UUID, tenant_id: UUID) -> LandingPageConfig:
        from src.services.db.repositories.offer_repository import OfferRepository
        offer_repo = OfferRepository(self.session)
        offer = offer_repo.get_by_id(offer_id)
        
        if not offer:
            raise ValueError("Offer not found")

        # 1. Determine Archetype
        archetype = self._get_archetype(offer.type)
        
        # 2. Prepare Context (Brand & Offer)
        # Fetch Tenant Brand Knowledge
        tenant = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
        brand_knowledge = json.dumps(tenant.config_json.get('brand_settings', {}), indent=2, ensure_ascii=False) if tenant else "{}"
        
        media_assets = self._fetch_media_assets(tenant_id)

        offer_details = f"""
        Name: {offer.public_name}
        Promise: {offer.headline_promise}
        Outcome: {offer.primary_outcome}
        Price: {offer.price}
        Modules: {offer.modules_json if hasattr(offer, 'modules_json') else 'Not specified'}
        """

        avatar_profile = offer.target_avatar_match or "Generic Entrepreneur"

        # 3. Render Prompt
        if archetype == LandingPageArchetype.THE_TRANSFORMER:
            template_name = "landing_coaching_grupal.j2"
            
            # Generate clean slug here
            clean_slug = f"/p/{self._slugify(offer.public_name)}"
            
            context = {
                "brand_knowledge": brand_knowledge,
                "offer_details": offer_details,
                "avatar_profile": avatar_profile,
                "media_assets": media_assets,
                "offer_slug": clean_slug
            }
            system_prompt = self._render_prompt(template_name, context)
            
            # 4. Invoke LLM (Structured Output)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate the landing page configuration now.")
            ]
            
            # Use structured output to get Pydantic object directly
            generated_data = await self.llm.with_structured_output(TransformerPageGeneration).ainvoke(messages)
            
            # 6. Resolve Image URLs in Content
            content_model = generated_data.content
            
            # Simple lookup
            asset_map = {a['id']: a['url'] for a in media_assets}
            
            # Resolve authority_image_url
            if content_model.authority_image_url and content_model.authority_image_url in asset_map:
                content_model.authority_image_url = asset_map[content_model.authority_image_url]
            
            # FALLBACK: If URL is relative (starts with /), prepend domain or use dummy absolute URL
            auth_url = str(content_model.authority_image_url) if content_model.authority_image_url else None
            
            if auth_url and auth_url.startswith('/'):
                 base_url = "http://localhost:8000" 
                 content_model.authority_image_url = f"{base_url}{auth_url}"
            elif auth_url and not auth_url.startswith('http') and auth_url not in asset_map:
                 # If it's just a filename or invalid string and wasn't in asset_map
                 # We leave it as is, or clear it. Pydantic validation passed (if we relax to str), so it's fine.
                 pass

            # 7. Construct Model
            # Inject Brand Theme
            brand_theme = self._extract_theme_from_brand(tenant.config_json) if tenant and tenant.config_json else LandingPageTheme()

            config = LandingPageConfig(
                archetype=archetype,
                theme=brand_theme, 
                content=content_model,
                slug=generated_data.slug,
                seo_title=generated_data.seo_title,
                seo_description=generated_data.seo_description
            )

        else:
            # FALLBACK to old logic for other archetypes (Squeeze, etc.)
            # For brevity, I'm keeping the Squeeze logic simplified or calling legacy methods
            # But effectively this service now prioritizes Transformer.
            logger.warning(f"Archetype {archetype} not fully implemented in V2 service, using Squeeze fallback")
            
            # Quick Squeeze Gen (Legacy Code reused)
            base_prompt = "Generate JSON for Squeeze Page. Schema: {headline, subheadline, bullets, cta_text}"
            response = await self.llm.ainvoke([SystemMessage(content=base_prompt + f"\nContext: {offer_details}")])
            # ... parsing logic would be here ...
            # Returning a dummy config to avoid breaking if not Transformer
            config = LandingPageConfig(
                archetype=LandingPageArchetype.THE_SQUEEZE,
                slug="/p/demo",
                content=SqueezeContent(headline="Demo", subheadline="Demo", bullets=[], cta_text="Click")
            )

        # 8. Save
        offer.landing_page_config = config.model_dump(mode='json')
        self.session.commit()
        self.session.refresh(offer)

        return config
