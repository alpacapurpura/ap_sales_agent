# Módulo de Assets (Gestión de Archivos & Galería) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la FUENTE DE VERDAD para entender cómo se gestionan, almacenan y procesan los archivos (imágenes, documentos, multimedia) en el sistema. Úsalo cuando necesites implementar subida de archivos, recuperar recursos para una landing page, o entender cómo un agente de ventas obtiene información de un PDF.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/assets/`
  - Dominio (entidad, enums): `domain/`
  - Servicio principal y procesador IA: `application/`
  - Modelo SQL y repositorio: `infrastructure/`
  - Endpoints: `api/`
- **Frontend**:
  - Cliente API central: `frontend/src/lib/api/` (buscar archivo relacionado con assets)
  - Componentes de galería/uploader: reutilizados en `frontend/src/features/brand/` y `frontend/src/features/offer-studio/`

## 2. Lógica de Negocio (The "Why" & "How")

### Centralización y Abstracción
- **Por qué**: Evitar duplicidad de lógica de almacenamiento (S3 vs Local) y validación de seguridad en cada módulo.
- **Cómo**: Todos los archivos pasan por `AssetsService`. Los otros módulos (Brand, Offer) solo guardan referencias (IDs o URLs).

### Procesamiento Asíncrono con IA
- **Flujo**:
  1.  Usuario sube archivo -> Backend guarda en disco/S3 -> Retorna `Asset` con estado `PROCESSING`.
  2.  **Background Task**: Se lanza un proceso de IA (Vision API / LLM).
  3.  **Enriquecimiento**: El proceso actualiza el registro en DB con `ai_metadata` (descripción, colores, OCR).
  4.  **Estado Final**: El asset pasa a estado `COMPLETED`.
- **Implicación**: La UI debe ser reactiva y manejar el estado "Procesando" (spinners o placeholders).

### Almacenamiento (Storage Strategy)
- **Híbrido**: Soporta `LOCAL` (sistema de archivos, para dev/on-premise) y `S3` (nube, para prod).
- **Resolución de URL**: El campo `public_url` en la BD ya es la URL final accesible (o relativa si es local). El frontend no debe construir URLs manualmente concatenando strings.

## 3. Integración entre Módulos (Cross-Module Interaction)

### ¿Cómo deben interactuar otros módulos con Assets?
La regla de oro es **Desacoplamiento Referencial**.

#### Escenario A: Landing Page (Frontend) quiere mostrar imágenes
- **Caso de uso**: Mostrar logos, banners o imágenes de producto.
- **Mecanismo**: La Landing Page debe solicitar los assets filtrando por `tenant_id` y `type` (o tags si existieran).
- **Flujo**:
  1.  Llamar a `assetsApi.list(token, type="IMAGE")`.
  2.  Usar la propiedad `public_url` de cada objeto `Asset`.
  3.  Si se requiere texto alternativo (alt text), usar `ai_description` o `user_description`.

#### Escenario B: Sales Agent (Backend) necesita enviar un PDF o Audio
- **Caso de uso**: Un bot de ventas necesita enviar un brochure técnico al usuario.
- **Mecanismo**: El agente busca en la base de datos de assets usando metadatos semánticos.
- **Flujo**:
  1.  Inyectar `AssetRepository` en el servicio del agente.
  2.  Ejecutar consulta: `repo.get_by_tenant(tenant_id, type=AssetType.DOCUMENT)`.
  3.  Filtrar en memoria o DB por `filename` o `ai_metadata` que coincida con la intención del usuario (ej: "catálogo").
  4.  Obtener `public_url` y enviarla al canal de chat.

#### Escenario C: Brand Module (Configuración)
- **Caso de uso**: Guardar el logo de la empresa.
- **Mecanismo**: `BrandSettings` guarda la URL o el ID del asset.
- **Recomendación**: Guardar `asset_id` permite mantener la integridad referencial y actualizar la imagen sin cambiar la configuración de marca. Si se guarda solo la URL, se pierde el vínculo con los metadatos de IA.

## 4. Casos Borde y Gotchas (Edge Cases)

- **Latencia de IA**: Un asset recién subido puede no tener `ai_metadata` disponible inmediatamente. Los consumidores deben ser tolerantes a fallos o campos vacíos en `ai_metadata`.
- **Seguridad y MIME Types**: El sistema valida el `magic number` del archivo, no solo la extensión. Renombrar `exe` a `jpg` fallará.
- **Borrado en Cascada**: Actualmente, si se borra un asset, los módulos que guardan solo la URL (como Brand en algunos casos legacy) se quedarán con un enlace roto.
  - **Solución**: Usar `asset_id` siempre que sea posible para validar integridad antes de borrar.

## 5. Snippets para Agentes (Common Tasks)

### Frontend: Subir un archivo y obtener su ID
```typescript
// ⚠️ Verificar nombres exactos de componentes/hooks en el código real antes de usar
import { assetsApi } from "@/lib/api/assets";

const handleUpload = async (file: File) => {
  try {
    // Subida directa
    const asset = await assetsApi.upload(token, file, "Logo de la empresa");
    console.log("Asset ID:", asset.id);
    console.log("URL Pública:", asset.public_url);
    
    // Guardar referencia en otro módulo
    updateBrandLogo(asset.id); 
  } catch (error) {
    console.error("Error subiendo asset:", error);
  }
};
```

### Backend: Buscar assets para un Agente
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# En un servicio de Sales Agent
from src.modules.assets.infrastructure.repositories.asset_repository import AssetRepository
from src.modules.assets.domain.enums import AssetType

async def get_brochure_url(tenant_id: UUID, topic: str) -> Optional[str]:
    assets = await asset_repository.get_by_tenant(tenant_id)
    
    # Filtrado simple en memoria (idealmente sería búsqueda vectorial si hay muchos)
    for asset in assets:
        if asset.type == AssetType.DOCUMENT and topic in (asset.ai_metadata.get("summary", "") or ""):
            return asset.public_url
            
    return None
```
