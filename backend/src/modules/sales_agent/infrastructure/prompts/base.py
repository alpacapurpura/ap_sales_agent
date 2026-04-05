import datetime
import logging
import os
from typing import Any
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import desc, select

from src.core.config import settings
from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.core.enums import PromptSource
from src.modules.iam.infrastructure.models.tenant_model import TenantModel as Tenant
from src.modules.sales_agent.infrastructure.models.prompt_version_model import (
    PromptVersion,
)

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Gestor de Prompts Híbrido Multitenant (DB + Caché + Archivo).
    Controlado por settings.PROMPT_SOURCE (Hybrid, File, DB).
    """

    def __init__(
        self,
        templates_dir: str = "src/modules/sales_agent/infrastructure/prompts/templates",
    ):
        # 1. Configurar File System Loader (Fallback)
        base_path = os.getcwd()
        self.templates_dir = templates_dir
        full_path = os.path.join(base_path, templates_dir)

        self.fs_env = Environment(
            loader=FileSystemLoader(full_path),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 2. Caché en Memoria Multitenant
        # Estructura: { (key, tenant_id): {"content": "...", "version": 1, "loaded_at": timestamp} }
        self._cache: dict[tuple[str, UUID | None], dict[str, Any]] = {}

        # 3. Caché de Configuración de Tenant (para evitar query en cada render)
        self._tenant_config_cache: dict[UUID, dict[str, Any]] = {}

    def _get_tenant_config(self, tenant_id: UUID) -> dict[str, Any]:
        """Recupera la configuración del Tenant (variables globales)."""
        # Check cache
        if tenant_id in self._tenant_config_cache:
            # Simple TTL logic could be added here
            return self._tenant_config_cache[tenant_id]

        db = SessionLocal()
        try:
            tenant = (
                    db.execute(select(Tenant).where(Tenant.id == tenant_id))
                    .scalars()
                    .first()
                )
            config = tenant.config_json if tenant and tenant.config_json else {}
            self._tenant_config_cache[tenant_id] = config
            return config
        except Exception as e:
            logger.warning(f"Error loading tenant config: {e}")
            return {}
        finally:
            db.close()

    def _get_from_db(self, key: str, tenant_id: UUID | None) -> str | None:
        """Intenta recuperar el prompt activo de la BD (Specific -> Default)."""
        db = SessionLocal()
        try:
            # 1. Intentar Tenant Specific Override
            if tenant_id:
                prompt = (
                    db.execute(
                        select(PromptVersion)
                        .where(
                            PromptVersion.key == key,
                            PromptVersion.is_active,
                            PromptVersion.tenant_id == tenant_id,
                        )
                        .order_by(desc(PromptVersion.version))
                    )
                    .scalars()
                    .first()
                )

                if prompt:
                    self._update_cache(key, tenant_id, prompt)
                    return prompt.content

            # 2. Intentar System Default (Fallback)
            prompt = (
                db.execute(
                    select(PromptVersion)
                    .where(
                        PromptVersion.key == key,
                        PromptVersion.is_active,
                        PromptVersion.tenant_id.is_(None),
                    )
                    .order_by(desc(PromptVersion.version))
                )
                .scalars()
                .first()
            )

            if prompt:
                self._update_cache(key, tenant_id, prompt)
                return prompt.content

            return None
        except Exception as e:
            logger.warning(f"Error loading prompt '{key}' from DB: {e}")
            return None
        finally:
            db.close()

    def _update_cache(self, key: str, tenant_id: UUID | None, prompt: PromptVersion):
        self._cache[(key, tenant_id)] = {
            "content": prompt.content,
            "version": prompt.version,
            "loaded_at": datetime.datetime.now().timestamp(),
        }

    def _load_from_file(self, key: str, template_name: str, **kwargs: Any) -> str:
        """Carga y renderiza directamente desde archivo."""
        fname = f"{key}.j2" if not template_name.endswith(".j2") else template_name
        template = self.fs_env.get_template(fname)
        return template.render(**kwargs)

    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Renderiza un prompt con las variables inyectadas + Contexto Tenant.
        """
        # Normalizar key
        key = template_name.replace(".j2", "")
        mode = settings.PROMPT_SOURCE

        # Obtener Tenant Context
        tenant_id = get_tenant_id()

        # Inyectar Variables del Tenant (Auto-Configuration)
        if tenant_id:
            tenant_config = self._get_tenant_config(tenant_id)
            # Merge: kwargs tiene prioridad sobre config del tenant
            # (aunque idealmente config del tenant son "constantes" para ese tenant)
            # Vamos a hacer que kwargs sobreescriba config por si acaso.
            full_context = {**tenant_config, **kwargs}
        else:
            full_context = kwargs

        # 1. Modo FILE: Ignorar DB
        if mode == PromptSource.FILE:
            return self._load_from_file(key, template_name, **full_context)

        # 2. Modo DB/Hybrid
        template_content = None
        cache_key = (key, tenant_id)

        # A. Intentar Caché
        TTL_SECONDS = 60
        if cache_key in self._cache:
            last_load = self._cache[cache_key].get("loaded_at", 0)
            if datetime.datetime.now().timestamp() - last_load < TTL_SECONDS:
                template_content = self._cache[cache_key]["content"]

        # B. Intentar DB
        if not template_content:
            template_content = self._get_from_db(key, tenant_id)

        # C. Renderizar
        try:
            if template_content:
                template = self.fs_env.from_string(template_content)
                return template.render(**full_context)
            if mode == PromptSource.DB:
                raise ValueError(f"Prompt '{key}' not found in DB (Strict Mode)")

            # Fallback a archivo (System Defaults locales)
            return self._load_from_file(key, template_name, **full_context)

        except Exception as e:
            logger.error(f"Error rendering prompt '{key}': {e}")
            if mode != PromptSource.DB:
                return self._load_from_file(key, template_name, **full_context)
            raise e

    def invalidate_cache(self, key: str):
        """Limpia caché (OJO: Limpia para TODOS los tenants por seguridad o solo uno?)"""
        # Simple: Limpiar todo lo relacionado a esa key
        keys_to_remove = [k for k in self._cache if k[0] == key]
        for k in keys_to_remove:
            del self._cache[k]


prompt_loader = PromptLoader()
