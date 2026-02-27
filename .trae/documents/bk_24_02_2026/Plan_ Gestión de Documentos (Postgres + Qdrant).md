# Plan Refinado: Gestión Multi-Colección y Ciclo de Vida Documental

Este plan incorpora la arquitectura de 3 colecciones especializadas ("Truth", "Psychology", "Objections") y permite su gestión dinámica desde la interfaz de administración.

## Análisis de la Estrategia Multi-Colección

**¿Es necesario separar en 3 colecciones físicas?**
No estrictamente, pero **SÍ es altamente recomendado** para tu caso de uso "High-Ticket" por dos razones:

1. **Aislamiento Semántico**: Evita que preguntas sobre "precios" recuperen documentos de "tono de voz" solo porque usan palabras similares.
2. **Optimización de Búsqueda**: Permite usar estrategias de recuperación distintas (ej: búsqueda exacta para datos duros vs. semántica pura para psicología).

Sin embargo, para mantener la simplicidad y flexibilidad operativa, implementaremos un **enfoque híbrido flexible**:

* **Gestión por "Categoría de Colección"**: En lugar de *hardcodear* 3 colecciones, permitiremos crear colecciones arbitrarias y asignarles un "rol" o categoría.

***

## Fase 1: Capa de Datos (PostgreSQL)

*Objetivo: Trazabilidad de qué documento está en qué colección.*

1. **Modelo** **`documents`** **(`src/core/models.py`)**:

   * Campos: `id`, `filename`, `collection_name` (Nuevo), `category` (factural/style/objection), `upload_date`, `chunk_count`.
2. **Servicio** **`DocumentService`**:

   * Lógica para registrar cargas asociadas a una colección específica.

   * Lógica para eliminar registros y disparar el borrado en Qdrant.

## Fase 2: Actualización de Vector Store (`src/services/vector_store.py`)

*Objetivo: Soporte para gestión dinámica de colecciones.*

1. **Función** **`delete_collection(collection_name)`**: Permitir borrar una colección entera.
2. **Función** **`delete_vectors_by_source(collection_name, source_name)`**: Borrado granular de documentos dentro de una colección.
3. **Función** **`list_collections()`**: Obtener lista real desde Qdrant.

## Fase 3: Interfaz de Administración Avanzada (`src/admin/app.py`)

*Objetivo: Panel de control total sobre Colecciones y Documentos.*

1. **Sección: Gestión de Colecciones**:

   * **Crear Nueva Colección**: Input para nombre (ej: `visionarias_hard_data`) + Botón "Crear".

   * **Listar/Eliminar Colecciones**: Tabla con colecciones existentes y botón de borrado (¡Peligro!).
2. **Sección: Carga de Documentos (Mejorada)**:

   * **Selector de Colección Destino**: Dropdown con las colecciones activas en Qdrant.

   * **Etiquetado Automático**: Al cargar, asignar metadata `category` basada en la selección (o manual).
3. **Sección: Inventario de Documentos**:

   * Tabla interactiva (desde Postgres) filtrable por Colección.

   * Acción: **Eliminar Documento** (Borra de Postgres + Qdrant).

## Fase 4: Integración en el Cerebro (`src/core/nodes.py`)

*Objetivo: Que el agente sepa dónde buscar.*

1. **Router Inteligente**:

   * Si la intención es `pricing` -> Buscar en colección `Truth_Source_Hard`.

   * Si la intención es `objection` -> Buscar en `Objection_Handling_Scripts`.

   * Si es `general` -> Buscar en todas (o en una por defecto).
     *(Nota: Esta fase se dejará preparada a nivel de configuración, la implementación profunda en el router puede ser un paso posterior si se desea, por ahora nos enfocamos en la gestión/ingesta).*

***

### Resumen Técnico

* **Base de Datos**: Nueva tabla `documents` en Postgres.

* **Qdrant**: Métodos para borrado granular y gestión de colecciones.

* **Admin UI**: Selectores dinámicos de colección y gestión de inventario.

