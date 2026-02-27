# Confirmación y Refactorización Arquitectónica

## Análisis de Estructura de Carpetas
He revisado tu estructura actual (`src/admin`, `src/core`, `src/services`, `src/api`) y **es sólida**. Sigue una arquitectura por capas limpia:
- **Core**: Cerebro del agente (Lógica pura).
- **Services**: Infraestructura y acceso a datos.
- **Admin**: Capa de presentación (UI).

**Veredicto**: No necesitamos mover carpetas ni cambiar la jerarquía de directorios. Hacerlo solo introduciría riesgos innecesarios ("malograr imports"). La mejora clave está en **cómo distribuimos la lógica dentro de esta estructura existente**.

## Plan de Ejecución

### 1. Nuevo Servicio: `src/services/knowledge_service.py`
Crearemos este archivo para centralizar la lógica de negocio que hoy "contamina" el frontend.
- **Responsabilidad**: Orquestar todo el ciclo de vida del conocimiento (Ingesta, Clasificación, Edición, Borrado).
- **Diseño**:
  - Clase `KnowledgeService`.
  - Método `ingest_file(...)`: Reemplaza a `process_upload`. Maneja lectura de archivos, estrategias de chunking y llamadas a Qdrant/DB.
  - Método `classify_content(...)`: Reemplaza a `auto_classify_document`.
  - Método `sync_category(...)`: Actualiza DB y Vector Store atómicamente.

### 2. Limpieza de `src/admin/app.py`
Transformaremos el Admin Panel en una "Vista Tonta" (Passive View Pattern).
- **Eliminar**: Importaciones de `langchain`, `qdrant_client`, `RecursiveCharacterTextSplitter`.
- **Integrar**: Instanciar `KnowledgeService` y llamar a sus métodos.
- **UI**: Mantener los widgets de Streamlit (barras de progreso, selectores), pero alimentados por el servicio.

### 3. Resultado Final (Estructura Lógica)
```text
src/
├── admin/
│   └── app.py            <-- SOLO Interfaz Gráfica (Limpio)
├── services/
│   ├── knowledge_service.py <-- NUEVO: Lógica de Ingesta y Gestión
│   ├── vector_store.py   <-- DAO de Qdrant (Bajo nivel)
│   ├── document_service.py <-- DAO de Postgres (Bajo nivel)
│   └── ...
└── ...
```
Esta estructura respeta los principios **KISS** (Keep It Simple, Stupid) y **Clean Code**, facilitando el mantenimiento sin romper la compatibilidad actual.
