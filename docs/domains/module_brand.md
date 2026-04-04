---
module: Brand
status: active
---

# Brand

Captura y estructura la identidad completa de marca del tenant. Alimenta al Sales Agent (personalidad), Assets (copies) y Copilot (auto-fill).

## Domain Concepts

- **BrandSettings**: Agregado raiz con 10 sub-modelos: `identity` (nombre, logo, sector), `strategy` (metodologia, pilares), `story` (origen, mision, vision), `team` (List[KeyFigure]), `positioning` (Brand Love Key — esencia, insight, beneficios, valores), `narrative` (StoryBrand — hero, problem, guide, plan, CTA, outcome), `communication_assets` (taglines, CTAs, hooks por etapa de funnel), `visuals` (colores, fuentes, design tokens), `contact`, `testimonials`, `authority_vault`.
- **ExtractionOrchestrator**: Coordina extraccion multi-seccion via LLM en waves concurrentes (respeta TPM limits). Crawl paralelo: texto + CSS (para visuals). Merge inteligente preserva datos existentes.

## Architecture Decisions

- **JSONB en tabla `tenants`**: `BrandSettings` se almacena en `tenants.config_json['brand_settings']` — no tiene tabla propia. Permite iterar en la estructura sin migraciones.
- **Avatares SI tienen tabla propia** (`avatars`) por necesidad de relaciones y busquedas complejas.
- **Deep merge en PATCH**: El backend hace merge por claves, no sobrescribe todo el JSON. Listas (team, testimonials) se reemplazan completas si el payload tiene datos.

## Business Rules

- `brand_name` es obligatorio — sin el, la marca se considera "no configurada".
- **Health Score**: Porcentaje de completitud. Si es bajo, el Sales Agent puede operar con personalidad generica o negarse.
- El extractor tiene hard-limit de 8 minutos (scraping + LLM analysis).
- `model_validator` migra campos legacy (`strategy.unique_value_proposition` -> `positioning`) al vuelo.

## Edge Cases

- **`flag_modified` obligatorio**: SQLAlchemy no detecta cambios dentro de JSONB automaticamente. Siempre llamar `flag_modified(tenant, "config_json")` despues de mutar el dict.
- **Schema migration en runtime**: Si `BrandSettings` cambia en Python, JSONs antiguos en DB pueden romper Pydantic. El `model_validator(mode='before')` transforma datos legacy.
- **Alucinacion de estilos**: El extractor a veces inventa hex codes si no encuentra CSS claro — el usuario debe confirmar colores.

## CRITICAL — Do Not Violate

- Siempre usar `flag_modified(tenant, "config_json")` al mutar JSONB — sin esto, SQLAlchemy no persiste el cambio.
- Los 10 sub-modelos de `BrandSettings` se auto-descubren via introspection (Copilot). Agregar nuevos campos NO requiere cambios en Copilot.
