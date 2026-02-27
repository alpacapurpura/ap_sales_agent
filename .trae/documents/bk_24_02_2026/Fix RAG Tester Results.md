# Corrección del Probador RAG

## Análisis del Problema
La búsqueda en Qdrant falla porque el servicio de búsqueda (`vector_store.py`) impone un filtro obligatorio `client_id="visionarias"`, pero los documentos se indexan sin este campo en sus metadatos.

## Tareas Técnicas

### 1. Actualización de `src/services/vector_store.py`
- Modificar `add_texts` para incluir `client_id` en el payload de cada punto si no está presente.
- Ajustar `search_knowledge_base` para que el filtro `client_id` solo se aplique si el valor no es `None` o si se desea manejar multi-tenancy de forma consistente.
- Agregar trazas de log para verificar el conteo de hits de Qdrant antes del reranking con FlashRank.

### 2. Refuerzo en `src/admin/app.py`
- Verificar que la función `render_rag_tester` maneje correctamente los filtros opcionales para evitar enviar estructuras de filtrado vacías que puedan anular los resultados.

### 3. Verificación
- Realizar búsquedas de prueba en el "Probador RAG" con y sin filtros de categoría.
- Verificar en los logs del contenedor `visionarias_brain` que la consulta a Qdrant sea exitosa.