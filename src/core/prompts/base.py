import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any

class PromptLoader:
    """
    Gestor de Prompts Escalable usando Jinja2.
    Permite separar la lógica del texto y mantener los prompts en archivos .j2
    versionables con Git.
    """
    
    def __init__(self, templates_dir: str = "src/core/prompts/templates"):
        # Aseguramos que la ruta sea absoluta respecto al root del proyecto
        base_path = os.getcwd()
        full_path = os.path.join(base_path, templates_dir)
        
        self.env = Environment(
            loader=FileSystemLoader(full_path),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Renderiza un prompt con las variables inyectadas.
        Ejemplo: loader.render("sales_pitch.j2", customer_name="Chris")
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            # Fallback robusto o re-raise
            raise ValueError(f"Error rendering prompt template '{template_name}': {e}")

# Instancia global para importar en los nodos
prompt_loader = PromptLoader()
