# Implementación de Contextual Retrieval (Anthropic)

Vamos a actualizar la lógica de ingesta en `KnowledgeService` para implementar el patrón de **Contextual Retrieval**. Esto sustituirá el resumen global estático por un contexto dinámico y específico para cada chunk, mejorando drásticamente la precisión de búsqueda.

## Cambios en `src/services/knowledge_service.py`

### 1. Eliminación del Contexto Global
Eliminaremos la generación del `doc_context` que se basaba en las primeras 3000 palabras del documento.

### 2. Implementación de Ventana Deslizante
En lugar de procesar los chunks individualmente, iteraremos sobre ellos con acceso a sus vecinos (Anterior + Actual + Siguiente) para construir una "Ventana de Contexto".

### 3. Generación de Contexto por Chunk (LLM)
Para cada chunk, invocaremos al LLM con un prompt específico:
> "Aquí está un fragmento del documento {filename}. Aquí está el contexto que lo rodea: {window}. Por favor, da un breve contexto explicativo (2-3 oraciones) para situar este fragmento..."

### 4. Optimización de Performance
Dado que esto implica llamar al LLM N veces (donde N es el número de chunks), añadiremos reportes de progreso detallados en el callback `on_progress` para que el usuario no piense que el sistema se ha colgado.

## Reset de Base de Datos
Como solicitado, ejecutaremos un reset de la colección de Qdrant para limpiar los vectores antiguos que tienen el contexto "sesgado" y dejar el sistema listo para re-indexar con la nueva lógica.

## Pseudocódigo del Nuevo Loop
```python
raw_chunks = text_splitter.create_documents([full_text])

for i, chunk in enumerate(raw_chunks):
    # 1. Construir ventana (Prev + Current + Next)
    window_text = get_sliding_window(raw_chunks, i)
    
    # 2. Generar Contexto Específico
    specific_context = llm.generate(f"Contextualiza este fragmento...: {window_text}")
    
    # 3. Enriquecer
    chunk.page_content = f"{specific_context}\n\n{chunk.page_content}"
```

Este cambio alineará tu sistema con las recomendaciones de Anthropic (Sept 2024), reduciendo fallos de recuperación por falta de contexto local.
