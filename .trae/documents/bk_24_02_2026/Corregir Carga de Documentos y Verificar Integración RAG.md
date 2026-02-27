Voy a solucionar el problema de "Connection lost" y la desaparición del botón de carga en el Admin, asegurando que la documentación se integre correctamente con el nodo de generación.

### 1. Estabilizar la Carga de Documentos (`src/admin/app.py`)
El error "Connection lost" se debe a que el procesamiento de archivos (especialmente el modo "Avanzado") bloquea la interfaz de Streamlit por demasiado tiempo, provocando un timeout en la conexión.

*   **Optimización del Procesamiento**:
    *   Implementaré `st.status` para mostrar el progreso paso a paso (Lectura -> Contexto -> Chunking -> Indexación) y evitar que la UI parezca congelada.
    *   Añadiré validación de tamaño de archivo. Si el archivo es muy grande, sugeriré automáticamente el modo "Básico" para evitar timeouts.
    *   Refactorizaré la lógica del botón para asegurar que siempre esté visible cuando hay un archivo seleccionado.
*   **Manejo de Errores**: Envolveré la lógica de carga en un bloque `try-except` específico para capturar desconexiones y mostrar un mensaje amigable en lugar de crashear la app.

### 2. Verificación de Integración RAG (`src/core/nodes.py` y `src/services/vector_store.py`)
He revisado el código y confirmo que la lógica de recuperación ya está correctamente implementada, pero haré una pequeña validación final:
*   **Consistencia de Filtros**: El nodo `node_response_generation` aplica filtros por categoría (`doc_category`). Confirmaré que la carga en `process_upload` guarde estas categorías en el formato exacto que Qdrant espera (Listas vs Strings) para que el `MatchAny` funcione correctamente.
*   **Prueba de Acceso**: El usuario podrá usar el "Probador RAG" existente en el Admin para verificar inmediatamente que lo cargado es visible por el sistema.

### Resultado Esperado
*   El Admin ya no mostrará "Connection lost" al cargar archivos.
*   Tendrás una barra de progreso visual durante la carga.
*   El nodo `node_response_generation` tendrá acceso inmediato a la nueva documentación sin cambios en su código actual (ya que la lógica de búsqueda es correcta).
