# Plan: Visor de Chunks en Inventario

Para permitirte inspeccionar a fondo qué información (chunks) ha generado el sistema para cada documento, implementaremos un "Visor de Vectores" dentro de la vista de Inventario.

## Cambios Propuestos

### 1. Backend (`src/services/vector_store.py`)
Crearemos una nueva función para recuperar los datos "crudos" desde Qdrant:
- **Función:** `fetch_vectors_by_source(collection_name, filename, limit=100)`
- **Lógica:** Utilizará el método `scroll` de Qdrant para listar todos los puntos cuyo metadato `source` coincida con el archivo seleccionado. Retornará el ID, el contenido de texto y los metadatos asociados.

### 2. Frontend (`src/admin/app.py`)
Actualizaremos `render_inventory_view` para incluir una sección de inspección:
- **Ubicación:** Justo debajo del formulario de edición de categorías, visible solo cuando seleccionas un documento.
- **Visualización:**
    - Una tabla resumen con los chunks (ID parcial, primeros 100 caracteres del texto).
    - Un área de detalle (expander) para ver el **Texto Completo** de cada chunk.
    - Métricas rápidas: Total de chunks recuperados vs. esperados.

## Flujo de Usuario
1. Vas a "Inventario".
2. Seleccionas el checkbox "Editar" en un documento.
3. Debajo de las opciones de categoría, aparecerá un nuevo panel: **"🔎 Inspector de Contenido (Chunks)"**.
4. Al expandirlo, verás la lista de fragmentos de texto que el RAG utiliza para responder.

Esto te permitirá verificar si la información fue cortada correctamente o si falta contexto, cumpliendo tu objetivo de "ver para complementar".