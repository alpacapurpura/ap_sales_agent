Implementaré la funcionalidad de "Carga Masiva" con clasificación automática por IA en el panel de administración.

### Plan de Implementación

1.  **Refactorización de Categorías (`src/admin/app.py`)**:
    *   Extraer la lista de categorías válidas a una constante global `VALID_CATEGORIES` al inicio del archivo para que sea accesible tanto por la vista de carga individual como por la masiva y el clasificador.

2.  **Nueva Función `auto_classify_document(text)`**:
    *   Implementar una función auxiliar que tome los primeros N caracteres del documento.
    *   Construir un prompt para el LLM (`LLMFactory`) pidiéndole que clasifique el texto en una de las `VALID_CATEGORIES`.
    *   Retornar la categoría sugerida.

3.  **Nueva Vista `render_bulk_upload_view()`**:
    *   Agregar un componente `st.file_uploader` con `accept_multiple_files=True`.
    *   Configurar por defecto la estrategia de chunking como "Avanzado".
    *   Implementar un bucle de procesamiento:
        *   Leer cada archivo.
        *   Llamar a `auto_classify_document` para obtener la categoría.
        *   Mostrar la categoría propuesta en la UI (feedback visual).
        *   Llamar a `process_upload` pasando la categoría sugerida.
        *   Manejar errores individualmente para no detener todo el lote si falla un archivo.

4.  **Actualización del Menú**:
    *   Agregar la opción "Carga Masiva" en el `st.sidebar` (radio button).
    *   Conectar la nueva opción en el router principal para mostrar `render_bulk_upload_view`.

Este enfoque cumple con todos los requisitos: ubicación en el menú, soporte múltiple, estrategia avanzada por defecto y uso de IA para la categorización.