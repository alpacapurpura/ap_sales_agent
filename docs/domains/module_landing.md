# Módulo de Landing Page (Offer Studio) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la FUENTE DE VERDAD para entender cómo se generan y gestionan las Landing Pages asociadas a ofertas. Úsalo para razonar sobre la transformación de "promesas de venta" en "activos visuales", la edición con Puck Editor y el renderizado público.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/landing/`
  - Schemas de arquetipos (THE_SQUEEZE, THE_TRANSFORMER, FLASH_OFFER): `domain/`
  - Servicio core de generación (Offer → Landing): `application/`
  - Modelo SQL (`landing_pages`) y repositorio: `infrastructure/`
  - Endpoints (GET por offer_id, POST config): `api/`
- **Frontend**: `frontend/src/features/offer-studio/components/landing/`
  - Editor visual (Puck): `components/editor/`
  - Templates de renderizado por arquetipo: `templates/`
  - Página pública SSR (acceso por slug): `frontend/src/app/(main)/(public)/p/`

## 2. Lógica de Negocio (The "Why" & "How")

### Generación Automática (Offer -> Landing)
El sistema NO permite crear landings vacías. Siempre nacen de una `Offer` existente.
1.  **Trigger**: Al crear una oferta o solicitar la landing por primera vez.
2.  **Mapeo Inteligente**:
    - `Offer.headline_promise` -> `Landing.headline`
    - `Offer.primary_outcome` -> `Landing.subheadline`
    - `Offer.marketing_pain_points` -> `Landing.bullets` (Fascinations)
3.  **Resultado**: Un JSON `LandingPageConfig` pre-poblado que el usuario solo necesita refinar, no escribir desde cero.

### Persistencia Híbrida (Relacional + JSONB)
- **Relacional**: `id`, `offer_id`, `slug`, `created_at` para búsquedas rápidas y relaciones SQL.
- **Documental (JSONB)**: El campo `config` almacena toda la estructura visual (colores, textos, orden de bloques).
- **Por qué**: Permite que el editor visual (Puck) sea extremadamente flexible y cambie su estructura sin migraciones de base de datos, mientras mantenemos la integridad referencial con la Oferta.

### Arquetipos de Landing
El sistema soporta múltiples "sabores" de landing, definidos en `content.py`:
- **THE_SQUEEZE**: Página corta, foco en captura de lead (Headline + Bullets + Form).
- **THE_TRANSFORMER**: Página larga, foco en educación y cambio de creencias (VSL + Testimonios + Oferta).
- **FLASH_OFFER**: Página de venta directa con urgencia temporal.

## 3. Casos Borde y Gotchas (Edge Cases)

- **Desincronización Oferta-Landing**:
  - Si el usuario cambia el `headline` en la Oferta, la Landing **NO** se actualiza automáticamente para no sobrescribir ediciones manuales en el editor visual.
  - **Solución**: El usuario debe solicitar explícitamente "Regenerar" o actualizar manualmente el texto en el editor.
- **Unicidad del Slug**:
  - El `slug` se genera desde el título de la oferta. Si ya existe, el sistema debe manejar la colisión (ej. agregando un sufijo aleatorio), aunque la lógica actual confía en UUIDs o validación previa.
- **Hydration Mismatch en Puck**:
  - El editor visual carga componentes dinámicos que pueden diferir entre servidor y cliente. Usar componentes `client-only` o `useEffect` para inicializar el editor evita errores de hidratación en Next.js.
- **Imágenes en el Editor**:
  - Las imágenes subidas en el editor deben guardarse y referenciarse correctamente. El frontend usa `adapter.ts` para asegurar que las URLs sean válidas para el componente de imagen.

## 4. Snippets para Agentes (Common Tasks)

### Obtener configuración de landing por Slug (Backend)
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# En un servicio o caso de uso público
async def get_public_landing(slug: str, db: AsyncSession):
    stmt = select(LandingPageModel).where(LandingPageModel.slug == slug)
    result = await db.execute(stmt)
    landing = result.scalar_one_or_none()
    
    if not landing:
        raise NotFoundException("Landing not found")
        
    # Retorna el modelo Pydantic validado
    return LandingPageConfig(**landing.config)
```

### Regenerar Landing desde Oferta (Backend)
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# Forzar la regeneración sobrescribe la configuración actual
async def regenerate_landing(offer_id: str, db: AsyncSession):
    offer = await offer_repo.get(offer_id)
    # Lógica de mapeo
    new_config = LandingService.map_offer_to_config(offer)
    
    landing = await landing_repo.get_by_offer(offer_id)
    landing.config = new_config.model_dump()
    await db.commit()
```
