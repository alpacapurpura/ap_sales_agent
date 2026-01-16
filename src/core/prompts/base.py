import os
import logging
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from typing import Dict, Any, Optional
from src.config import settings
from src.core.schema import PromptSource
from src.services.database import SessionLocal
from src.services.models import PromptVersion
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

class PromptLoader:
    """
    Gestor de Prompts Híbrido (DB + Caché + Archivo).
    Controlado por settings.PROMPT_SOURCE (Hybrid, File, DB).
    """
    
    def __init__(self, templates_dir: str = "src/core/prompts/templates"):
        # 1. Configurar File System Loader (Fallback)
        base_path = os.getcwd()
        self.templates_dir = templates_dir
        full_path = os.path.join(base_path, templates_dir)
        
        self.fs_env = Environment(
            loader=FileSystemLoader(full_path),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 2. Caché Simple en Memoria
        # Estructura: { "sales_system": {"content": "...", "version": 1} }
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_from_db(self, key: str) -> Optional[str]:
        """Intenta recuperar el prompt activo de la BD."""
        db = SessionLocal()
        try:
            # Buscar el activo más reciente (aunque debería haber solo uno activo)
            prompt = db.execute(
                select(PromptVersion)
                .where(PromptVersion.key == key, PromptVersion.is_active == True)
                .order_by(desc(PromptVersion.version))
            ).scalars().first()
            
            if prompt:
                # Actualizar Caché
                self._cache[key] = {
                    "content": prompt.content,
                    "version": prompt.version,
                    "loaded_at": datetime.datetime.now().timestamp() # Timestamp para TTL
                }
                return prompt.content
            return None
        except Exception as e:
            logger.warning(f"Error loading prompt '{key}' from DB: {e}")
            return None
        finally:
            db.close()

    def _load_from_file(self, key: str, template_name: str, **kwargs: Any) -> str:
        """Carga y renderiza directamente desde archivo."""
        fname = f"{key}.j2" if not template_name.endswith(".j2") else template_name
        template = self.fs_env.get_template(fname)
        return template.render(**kwargs)

    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Renderiza un prompt con las variables inyectadas.
        La fuente depende de settings.PROMPT_SOURCE.
        """
        # Normalizar key (quitar extensión .j2 si viene)
        key = template_name.replace(".j2", "")
        mode = settings.PROMPT_SOURCE
        
        # 1. Modo FILE: Ignorar DB completamente
        if mode == PromptSource.FILE:
            return self._load_from_file(key, template_name, **kwargs)
            
        # 2. Modo DB/Hybrid: Intentar recuperar contenido
        template_content = None
        
        # A. Intentar Caché
        TTL_SECONDS = 60 
        if key in self._cache:
            last_load = self._cache[key].get("loaded_at", 0)
            if datetime.datetime.now().timestamp() - last_load < TTL_SECONDS:
                template_content = self._cache[key]["content"]
        
        # B. Intentar DB (Si no estaba en caché o expiró)
        if not template_content:
            template_content = self._get_from_db(key)
            
        # C. Renderizar o Fallback
        try:
            if template_content:
                # Renderizar string dinámico de DB
                template = self.fs_env.from_string(template_content)
                return template.render(**kwargs)
            else:
                # Si estamos en modo DB estricto y falló, lanzar error
                if mode == PromptSource.DB:
                    raise ValueError(f"Prompt '{key}' not found in DB (Strict Mode)")
                    
                # Si es Hybrid, fallback a archivo
                return self._load_from_file(key, template_name, **kwargs)
                
        except Exception as e:
            logger.error(f"Error rendering prompt '{key}': {e}")
            # Fallback final en caso de error de renderizado de DB
            if mode != PromptSource.DB:
                 return self._load_from_file(key, template_name, **kwargs)
            raise e

    def invalidate_cache(self, key: str):
        """Fuerza la recarga desde DB en la próxima llamada."""
        if key in self._cache:
            del self._cache[key]

# Instancia global para importar en los nodos
prompt_loader = PromptLoader()
