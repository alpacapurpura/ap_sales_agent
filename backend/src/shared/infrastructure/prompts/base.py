"""Hybrid prompt loader with DB, file, and cache resolution."""

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import text

from src.core.config import settings
from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.core.enums import PromptSource
from src.shared.domain.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load and render Jinja2 prompts from DB or filesystem with caching."""

    def __init__(
        self,
        templates_dir: str = "src/modules/copilot/infrastructure/prompts/templates",
    ) -> None:
        """Initialize the prompt loader with a templates directory."""
        base_path = Path.cwd()
        full_path = str(base_path / templates_dir)
        self.fs_env = Environment(
            loader=FileSystemLoader(full_path),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._cache: dict[tuple[str, UUID | None], dict[str, Any]] = {}
        self._tenant_config_cache: dict[UUID, dict[str, Any]] = {}

    def _get_tenant_config(self, tenant_id: UUID) -> dict[str, Any]:
        if tenant_id in self._tenant_config_cache:
            return self._tenant_config_cache[tenant_id]

        db = SessionLocal()
        try:
            result = (
                db.execute(
                    text(
                        "SELECT config_json FROM tenants WHERE id = :tenant_id LIMIT 1",
                    ),
                    {"tenant_id": str(tenant_id)},
                )
                .mappings()
                .first()
            )
            config = result["config_json"] if result and result.get("config_json") else {}
            self._tenant_config_cache[tenant_id] = config
        except Exception as exc:  # noqa: BLE001 — prompt loading resilience
            logger.warning("Error loading tenant config: %s", exc)
            return {}
        else:
            return config
        finally:
            db.close()

    def _update_cache(
        self,
        key: str,
        tenant_id: UUID | None,
        prompt: dict[str, Any],
    ) -> None:
        self._cache[(key, tenant_id)] = {
            "content": prompt["content"],
            "version": prompt.get("version", 1),
            "loaded_at": utc_now().timestamp(),
        }

    def _get_from_db(self, key: str, tenant_id: UUID | None) -> str | None:
        db = SessionLocal()
        try:
            if tenant_id:
                tenant_prompt = (
                    db.execute(
                        text(
                            """
                        SELECT content, version
                        FROM prompt_versions
                        WHERE key = :key
                          AND is_active = TRUE
                          AND tenant_id = :tenant_id
                        ORDER BY version DESC
                        LIMIT 1
                        """,
                        ),
                        {"key": key, "tenant_id": str(tenant_id)},
                    )
                    .mappings()
                    .first()
                )
                if tenant_prompt:
                    self._update_cache(key, tenant_id, tenant_prompt)
                    return tenant_prompt["content"]

            global_prompt = (
                db.execute(
                    text(
                        """
                    SELECT content, version
                    FROM prompt_versions
                    WHERE key = :key
                      AND is_active = TRUE
                      AND tenant_id IS NULL
                    ORDER BY version DESC
                    LIMIT 1
                    """,
                    ),
                    {"key": key},
                )
                .mappings()
                .first()
            )
            if global_prompt:
                self._update_cache(key, tenant_id, global_prompt)
                return global_prompt["content"]
        except Exception as exc:  # noqa: BLE001 — prompt loading resilience
            logger.warning("Error loading prompt '%s' from DB: %s", key, exc)
            return None
        else:
            return None
        finally:
            db.close()

    def _load_from_file(self, key: str, template_name: str, **kwargs: Any) -> str:  # noqa: ANN401 — template variable expansion
        filename = f"{key}.j2" if not template_name.endswith(".j2") else template_name
        template = self.fs_env.get_template(filename)
        return template.render(**kwargs)

    def render(self, template_name: str, **kwargs: Any) -> str:  # noqa: ANN401 — template variable expansion
        """Render a prompt template by name using the configured resolution strategy."""
        key = template_name.replace(".j2", "")
        mode = settings.PROMPT_SOURCE
        tenant_id = get_tenant_id()

        if tenant_id:
            tenant_config = self._get_tenant_config(tenant_id)
            full_context = {**tenant_config, **kwargs}
        else:
            full_context = kwargs

        if mode == PromptSource.FILE:
            return self._load_from_file(key, template_name, **full_context)

        template_content: str | None = None
        cache_key = (key, tenant_id)
        ttl_seconds = 60
        if cache_key in self._cache:
            last_load = self._cache[cache_key].get("loaded_at", 0)
            if utc_now().timestamp() - last_load < ttl_seconds:
                template_content = self._cache[cache_key]["content"]

        if not template_content:
            template_content = self._get_from_db(key, tenant_id)

        try:
            if template_content:
                template = self.fs_env.from_string(template_content)
                return template.render(**full_context)
            if mode == PromptSource.DB:
                msg = f"Prompt '{key}' not found in DB (Strict Mode)"
                raise ValueError(msg)  # noqa: TRY301
            return self._load_from_file(key, template_name, **full_context)
        except Exception:
            logger.exception("Error rendering prompt '%s'", key)
            if mode != PromptSource.DB:
                return self._load_from_file(key, template_name, **full_context)
            raise

    def invalidate_cache(self, key: str) -> None:
        """Remove all cached entries for the given prompt key."""
        keys_to_remove = [cache_key for cache_key in self._cache if cache_key[0] == key]
        for cache_key in keys_to_remove:
            del self._cache[cache_key]


prompt_loader = PromptLoader()
