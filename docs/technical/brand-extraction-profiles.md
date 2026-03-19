# Brand Extraction Profiles

## Contexto

La extraccion de marca (Brand Studio) ejecuta 6 llamadas LLM concurrentes para extraer identity, story, strategy, people/contact, testimonials y authority. Con modelos de rate-limit bajo (ej. `gpt-4-turbo-preview` con 30K TPM), lanzar las 6 en paralelo causa:

1. **Error 400**: `max_tokens is too large` si se pide mas de 4096 tokens de salida
2. **Error 429**: Rate limit exceeded (TPM) al saturar el presupuesto de tokens con 6 prompts de ~37K chars

Ambos errores son capturados silenciosamente por los `except Exception` de cada `_extract_*`, retornando modelos vacios. El resultado: extraccion "exitosa" pero con secciones vacias.

## Solucion: Extraction Profiles

Dos perfiles inmutables definidos en codigo, seleccionables por env var. Ambos siempre existen — solo se activa uno.

### Perfiles disponibles

| Parametro | `safe` (default) | `fast` |
|---|---|---|
| Concurrencia | 2 waves de 3 (pausa 5s entre waves) | 6 concurrent |
| Modelo | `smart` | `smart` |
| Max output tokens | 4,000 | 4,000 |
| Retries | 3 (delay base 3s) | 3 (delay base 1s) |
| Caso de uso | Rate limit bajo (30K TPM, gpt-4-turbo-preview) | Rate limit alto (>=150K TPM, gpt-4o, gpt-4o-mini) |

### Wave strategy (perfil `safe`)

```
Wave 1 (concurrent):  identity, story, testimonials
         |
    [5s pause — TPM budget recovery]
         |
Wave 2 (concurrent):  strategy, people_contact, authority
```

Wave 1 agrupa las extracciones mas ligeras. Wave 2 agrupa las mas pesadas (strategy y people_contact usan prompts mas largos).

## Configuracion

### Cambiar perfil

En `.env` o `docker-compose.yml`:

```env
BRAND_EXTRACTION_PROFILE=safe   # default — 2 waves, retries conservadores
BRAND_EXTRACTION_PROFILE=fast   # 6 concurrent, retries rapidos
```

El setting esta registrado en `src/core/config.py` como `BRAND_EXTRACTION_PROFILE`.

### Verificar perfil activo

Al iniciar una extraccion, el log `extraction_profile_loaded` muestra el perfil activo:

```json
{
  "event": "extraction_profile_loaded",
  "profile": "safe",
  "model_type": "smart",
  "max_output_tokens": 4000,
  "concurrency_waves": 2,
  "retries": 3
}
```

## Agregar un nuevo perfil

En `backend/src/modules/brand/application/extraction_service.py`:

```python
PROFILE_CUSTOM = ExtractionProfile(
    name="custom",
    model_type="fast",            # usa el modelo rapido (gpt-3.5-turbo)
    max_output_tokens=2000,
    retries=2,
    retry_delay_seconds=0.5,
    concurrency_waves=1,          # todo concurrent
    wave_delay_seconds=0,
)

# Registrar en el dict
_PROFILES = {
    "safe": PROFILE_SAFE,
    "fast": PROFILE_FAST,
    "custom": PROFILE_CUSTOM,
}
```

## Diagnostico: Pipeline de logging

Cada extraccion genera una traza completa en structlog (backend) y console.log (frontend):

### Backend (structlog)

```
extract_full_brand_request          — params del request (url, mode, file_count)
  extraction_profile_loaded         — perfil activo y sus parametros
  starting_crawl                    — inicio crawl de URL
  crawl_completed                   — paginas crawleadas, chars totales
  extraction_context_prepared       — contenido total listo
  starting_llm_extractions          — inicio de extracciones (waves/concurrent)
    extraction_wave_starting        — [solo safe] inicio de wave N
    prompt_rendered                 — template, prompt_length (x6)
    extract_*_starting              — prompt_length por seccion (x6)
    extract_*_success               — fields_extracted, field_count (x6)
    extract_*_failed                — error, traceback (si falla)
    extraction_wave_pause           — [solo safe] pausa entre waves
  extraction_results_summary        — resumen: cuantas OK vs failed
  merge_completed                   — summary post-merge
  brand_repo_saving                 — data_keys, has_identity, has_story
  brand_repo_saved_verified         — verificacion post-commit
  extraction_saved_to_db            — summary final
extract_full_brand_response         — response summary al API
```

### Frontend (console.log)

```
[SmartFill] Extraction result:     — post-API call, keys con data
[BrandAPI] extractFullBrand:       — response del endpoint
[BrandAPI] GET settings response:  — datos en el GET post-reload
[useBrandSettings] Final data:     — datos despues de aplicar defaults
```

### Diagnosticar un fallo

1. Buscar `extract_*_failed` en los logs — muestra traceback completo
2. Buscar `ai_action_retry` — muestra el error de OpenAI (400, 429, etc.)
3. Verificar `extraction_results_summary` — cuantas secciones tuvieron data
4. Comparar `merge_completed` vs `brand_repo_saved_verified` — si hay discrepancia, el problema es en persistencia

## Archivos involucrados

| Archivo | Rol |
|---|---|
| `backend/src/modules/brand/application/extraction_service.py` | Profiles, waves, logging, 6 extracciones |
| `backend/src/modules/brand/infrastructure/repositories/brand_repository.py` | Persistencia + logging de save/get |
| `backend/src/modules/brand/api/extraction.py` | Endpoint POST + logging request/response |
| `backend/src/modules/brand/api/router.py` | Endpoint GET + logging response |
| `backend/src/core/config.py` | `BRAND_EXTRACTION_PROFILE` setting |
| `frontend/src/features/brand/api/index.ts` | Console logging GET/extract |
| `frontend/src/features/brand/hooks/useBrandSettings.ts` | Console logging post-defaults |
| `frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx` | Console logging post-extraction |
