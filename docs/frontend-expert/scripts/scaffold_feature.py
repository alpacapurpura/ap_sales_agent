#!/usr/bin/env python3
import os
import argparse
from pathlib import Path

def create_fsd_structure(base_path: Path, feature_name: str):
    """
    Crea la estructura estandarizada de un slice FSD (Feature-Sliced Design).
    Contiene: ui, model, api, lib y el Public API (index.ts).
    """
    target_dir = base_path / feature_name
    
    if target_dir.exists():
        print(f"⚠️ El directorio {target_dir} ya existe. Abortando para evitar sobrescribir.")
        return

    # Subdirectorios estándar FSD
    subdirs = ["ui", "model", "api", "lib", "config"]
    
    for subdir in subdirs:
        dir_path = target_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Crear un archivo por defecto para mantener el directorio en git
        (dir_path / ".gitkeep").touch()

    # Public API index
    index_content = f"""// Public API para el slice {feature_name}
// Exporta aquí solo lo que el resto de la aplicación necesita consumir.

// export * from './ui/{feature_name}';
// export * from './model/types';
"""
    with open(target_dir / "index.ts", "w", encoding="utf-8") as f:
        f.write(index_content)

    # Componente UI por defecto
    ui_component = f"""import React from 'react';
import {{ cn }} from '@/shared/lib/utils';

export interface {feature_name.replace('-', ' ').title().replace(' ', '')}Props extends React.HTMLAttributes<HTMLDivElement> {{
  // Props específicas aquí
}}

export function {feature_name.replace('-', ' ').title().replace(' ', '')}({{ 
  className, 
  ...props 
}}: {feature_name.replace('-', ' ').title().replace(' ', '')}Props) {{
  return (
    <div className={{cn("flex flex-col", className)}} {{...props}}>
      {feature_name} implementado
    </div>
  );
}}
"""
    with open(target_dir / "ui" / f"{feature_name}.tsx", "w", encoding="utf-8") as f:
        f.write(ui_component)

    print(f"✅ Estructura FSD para '{feature_name}' creada exitosamente en {target_dir}")
    print("📁 Carpetas generadas: ui/, model/, api/, lib/, config/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de Slices FSD para el Frontend")
    parser.add_argument("name", help="Nombre del slice en kebab-case (ej. user-profile)")
    parser.add_argument("--layer", required=True, choices=['features', 'entities', 'widgets', 'pages'], help="Capa de FSD")
    parser.add_argument("--path", default="frontend/src", help="Ruta base de la capa (ej. frontend/src/features)")

    args = parser.parse_args()
    
    # Resolver la ruta correcta asegurando que estamos en la carpeta de la capa
    base_path = Path(args.path)
    if not base_path.name == args.layer:
        base_path = base_path / args.layer
        
    create_fsd_structure(base_path, args.name)