# Plan de Implementación: Sistema RAG de Alto Rendimiento "Visionarias Brain"

Este plan transforma el sistema actual de búsqueda simple en un pipeline **RAG Híbrido y Autocorrectivo (Self-Healing)**, e incluye una **Interfaz de Administración** para gestionar el conocimiento.

## Fase 1: Interfaz de Gestión de Conocimiento (Streamlit)

*Objetivo: Permitir la carga y gestión visual de documentos para "poblar el RAG".*

1. **Nuevo Servicio Admin**: Crear una app ligera con **Streamlit** en `src/admin/app.py`.
2. **Funcionalidades**:

   * **Upload**: Carga de archivos (PDF, Markdown, TXT).

   * **Chunking Visual**: Vista previa de cómo se divide el texto antes de indexar.

   * **Gestión**: Listar documentos indexados y botón para borrar/reindexar.
3. **Infraestructura**: Añadir servicio `admin` al `docker-compose.yml`.

## Fase 2: Infraestructura RAG Avanzada (Hybrid Search)

*Objetivo: Habilitar búsqueda por palabras clave (BM25) junto con vectores (Semántica).*

1. **Dependencias**: Actualizar `requirements.txt` con:

   * `fastembed` o `rank_bm25` (para vectores dispersos/sparse).

   * `flashrank` (para reranking ligero y rápido).
2. **Configuración Qdrant (`vector_store.py`)**:

   * Modificar `ensure_collection_exists` para habilitar vectores híbridos (Dense + Sparse).

   * Actualizar `add_texts` para generar ambos tipos de embeddings.

## Fase 3: Pipeline RAG en LangGraph (HyDE + Rerank + CRAG)

*Objetivo: Implementar la lógica de "Self-Healing" y optimización de respuestas.*

1. **Nodo HyDE (Hypothetical Document Embeddings)**:

   * Crear prompt `hyde_generator.j2`.

   * Generar una respuesta hipotética *antes* de buscar, para mejorar la precisión semántica.
2. **Recuperación Híbrida & Reranking**:

   * Actualizar `search_knowledge_base` para hacer **Hybrid Search** (0.7 Vector + 0.3 Keyword).

   * Implementar **Reranking** con `FlashRank` para reordenar los top 10 resultados y quedarse con los top 3 más relevantes.
3. **Lógica CRAG (Corrective RAG)**:

   * Evaluar la relevancia de los documentos recuperados.

   * Si la relevancia es baja (< umbral), activar fallback (reescribir query o indicar falta de info) en lugar de alucinar.

## Fase 4: Integración y Despliegue

1. **Actualizar Grafo (`agent.py`)**: Insertar los nuevos pasos en el flujo de `node_response_generation`.
2. **Validación**: Pruebas con preguntas complejas del negocio ("¿Qué diferencia hay con un curso normal?") para verificar la mejora en calidad.

***

### Resumen Técnico de Cambios

* **Archivos a crear**: `src/admin/app.py`, `src/admin/Dockerfile`.

* **Archivos a modificar**: `requirements.txt`, `docker-compose.yml`, `src/services/vector_store.py`, `src/core/nodes.py`.

