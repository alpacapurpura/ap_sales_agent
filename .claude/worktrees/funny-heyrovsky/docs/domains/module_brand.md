# Módulo de Marca (Brand Studio) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la FUENTE DE VERDAD para entender cómo funciona la identidad de marca en el sistema. Úsalo para razonar sobre problemas de "personalidad del bot", "estilos visuales" o "configuración de empresa".

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/brand/`
  - Agregados y value objects de dominio: `domain/`
  - Repositorio (lee/escribe JSONB en tabla `tenants`): `infrastructure/repositories/`
  - API (GET, PATCH con deep-merge, POST /extract): `api/`
- **Frontend**: `frontend/src/features/brand/`
  - Hook de estado global: `hooks/`
  - Tipos TypeScript (espejo de Pydantic): `types/`
  - Componentes del studio: `components/`

## 2. Lógica de Negocio (The "Why" & "How")

### Almacenamiento (Persistence Strategy)
- **Híbrido**:
  - La configuración general (`BrandSettings`) vive en un campo **JSONB** (`config_json`) en la tabla `tenants`. NO tiene tabla propia.
  - Los **Avatares** (Buyer Personas) SÍ tienen tabla propia (`avatars`) por necesidad de relaciones y búsquedas complejas.
- **Por qué**: Permite iterar rápido en la estructura de la marca sin migraciones de base de datos.

### Reglas Críticas (Business Rules)
1.  **Identidad Mínima**: `brand_name` es obligatorio. Sin él, el sistema considera la marca "no configurada".
2.  **Health Score**: El sistema calcula un porcentaje de completitud. Si es bajo, los agentes de ventas pueden negarse a operar o funcionar con personalidad genérica.
3.  **Inmutabilidad Parcial**: Al actualizar, el backend hace un "merge" inteligente. No se sobrescribe todo el JSON, solo las claves enviadas.

### Flujo de Extracción (Extraction Agent)
1.  Usuario provee URL.
2.  Backend lanza `BrowserService` (Headless Chrome) para scrapear texto e imágenes.
3.  LLM analiza el contenido y estructura un objeto `BrandSettings` preliminar.
4.  Frontend recibe el objeto y pre-llena los formularios para validación humana.
5.  **Timeout**: El proceso tiene un hard-limit de 8 minutos debido a la latencia de scraping + análisis profundo.

## 3. Casos Borde y Gotchas (Edge Cases)

- **Alucinación de Estilos**: El extractor a veces inventa códigos hexadecimales si no encuentra estilos CSS claros. El usuario siempre debe confirmar los colores.
- **Imágenes Relativas vs Absolutas**: Las URLs de logos guardadas deben ser absolutas o manejarse con el helper `getFullUrl` en frontend.
- **Migración de Esquema**: Si cambiamos `BrandSettings` en Python, los JSONs antiguos en DB pueden romper Pydantic.
  - **Solución**: Usar `root_validator(pre=True)` en Pydantic para transformar datos legacy al vuelo.

## 4. Snippets para Agentes (Common Tasks)

### Cómo obtener la marca en Backend
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# En un servicio o caso de uso
tenant = await tenant_repo.get_by_id(tenant_id)
brand_settings = BrandSettings(**tenant.config_json.get("brand_settings", {}))
print(brand_settings.identity.brand_name)
```

### Cómo actualizar un campo parcial
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# El repositorio se encarga del merge, pero conceptualmente:
current_settings = tenant.config_json.get("brand_settings", {})
current_settings.update(new_data)
tenant.config_json["brand_settings"] = current_settings
flag_modified(tenant, "config_json") # Crucial para SQLAlchemy
```
