Para permitir modificar las categorías de los documentos desde el "Inventario" y sincronizar estos cambios con Qdrant, necesito realizar las siguientes acciones:

### 1. Actualizar `src/services/document_service.py`
Implementar un método `update_document_category` que:
*   Reciba `filename` y `new_categories` (lista).
*   Busque el registro en PostgreSQL y actualice la columna `category`.
*   Esto mantiene la consistencia en la base de datos relacional.

### 2. Actualizar `src/services/vector_store.py`
Implementar un método `update_vectors_category` que:
*   Reciba `filename` y `new_categories`.
*   Utilice la API de Qdrant (`qdrant_client.set_payload`) para actualizar el campo `doc_category` en **todos** los vectores asociados a ese archivo (filtrando por `source == filename`).
*   Esto asegura que el RAG use las nuevas categorías inmediatamente.

### 3. Modificar `src/admin/app.py`
En la función `render_inventory_view`:
*   Cambiar la configuración de `st.data_editor` para que la columna "Categoría" sea editable (usando `st.column_config.ListColumn` o `SelectboxColumn` si es posible, o texto libre validado). Dado que las categorías son etiquetas múltiples, usaremos una configuración que permita edición.
*   Detectar cambios en el DataFrame editado.
*   Si hay cambios, llamar a los nuevos servicios creados para actualizar tanto Postgres como Qdrant.
*   Mostrar un mensaje de éxito al usuario.

Este enfoque garantiza que la metadata esté sincronizada en ambos sistemas (SQL y Vectorial) sin necesidad de re-indexar todo el documento.