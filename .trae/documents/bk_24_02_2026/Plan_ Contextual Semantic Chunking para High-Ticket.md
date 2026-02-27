# Plan de Implementación: Contextual Semantic Chunking (High-Fidelity)

Este plan actualiza la interfaz de administración (`src/admin/app.py`) y la lógica de ingesta para implementar una estrategia de "Chunking Semántico Contextual", ideal para ventas High-Ticket donde el contexto es crítico.

## Fase 1: Actualización de Dependencias

*Objetivo: Habilitar el uso de splitters semánticos experimentales de LangChain.*

1. **Editar `requirements.txt`**:
   *   Agregar `langchain-experimental`.

## Fase 2: Implementación de Lógica de Ingesta Contextual

*Objetivo: Reemplazar el `RecursiveCharacterTextSplitter` con un pipeline de dos pasos: Resumen Global + Corte Semántico.*

1. **Modificar `src/admin/app.py`**:
   *   **Nuevo Selector de Estrategia**: Permitir elegir entre "Básico (Recursivo)" y "Avanzado (Semántico Contextual)".
   *   **Integrar `SemanticChunker`**: Usar `OpenAIEmbeddings` (reutilizando la factory existente) para detectar cambios de tema reales.
   *   **Generador de Contexto Global**: Implementar la función `generate_global_context` usando un modelo rápido (`gpt-4o-mini` o el configurado como default) para crear un resumen del documento.
   *   **Inyección de Contexto**: Concatenar el resumen global al inicio de *cada* chunk generado.

## Fase 3: Ajuste de Interfaz de Usuario (Streamlit)

*Objetivo: Dar control al usuario sobre la granularidad del chunking semántico.*

1. **Controles Avanzados (Solo visibles si se elige Chunking Semántico)**:
   *   Slider para `breakpoint_threshold_amount` (Percentil): Default 95, rango 50-100.
   *   Visualización del "Contexto Global Generado" para validación manual antes de indexar.

## Fase 4: Validación y Pruebas

1. **Prueba de Flujo**:
   *   Subir un PDF de ventas.
   *   Verificar que se genere un resumen coherente ("Este documento es sobre el Programa Alpha...").
   *   Comprobar en el preview que cada chunk empiece con "CONTEXTO DEL DOCUMENTO: ...".
   *   Indexar y confirmar en Qdrant.

***

### Resumen Técnico

*   **Librerías Nuevas**: `langchain-experimental`.
*   **Modelos**:
    *   *Contexto*: Reutilizar `LLMFactory.get_service().generate_response` (o instanciar uno ligero si se prefiere separar costos).
    *   *Embeddings*: Reutilizar `LLMFactory.get_service().get_embedding_model()`.
*   **Prompt de Contexto**: Se adaptará el prompt sugerido para resaltar "exclusiones y condiciones" (High-Ticket safe).

