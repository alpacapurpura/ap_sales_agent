# Plan de Mejora: Filtrado Híbrido Dinámico (Hard Data + Soft Skills)

Este plan optimiza el sistema actual para que maneje consultas de ventas complejas aplicando una estrategia de filtrado "OR" inteligente y segregación de tipos de datos.

## Fase 1: Optimización del Router de Intenciones (`src/core/nodes.py`)

*Objetivo: Mejorar la detección de intención para aplicar los filtros correctos.*

1.  **Refinar `node_response_generation`**:
    *   Expandir la lógica heurística actual para cubrir más casos de uso.
    *   **Caso Precios/Datos**: Si detecta "precio", "fecha", "garantía" -> Filtro estricto `hard_fact`.
    *   **Caso Emocional/Objeciones**: Si detecta "miedo", "no sé", "pensar", "esposo" -> Filtro amplio `['script', 'soft_skill']`.
    *   **Caso Mixto**: Si la consulta es ambigua, usar un filtro que incluya todas las categorías relevantes o eliminar el filtro para búsqueda global.

## Fase 2: Verificación de Ingesta y Metadatos

*Objetivo: Asegurar que los datos existentes soportan la nueva estrategia.*

1.  **Validación**: Confirmar que los documentos subidos tengan los metadatos `doc_category` correctos (`hard_fact`, `soft_skill`, `script`).
    *   *Acción*: Usar el Admin Panel para verificar el inventario. Si faltan metadatos, recomendar re-ingesta.

## Fase 3: Pruebas de Recuperación (Retrieval Testing)

*Objetivo: Validar que la lógica "OR" funciona como se espera.*

1.  **Caso de Prueba A (Hard Data)**: Preguntar "¿Cuál es el precio?" -> Debe recuperar solo docs de `hard_fact`.
2.  **Caso de Prueba B (Soft Skill)**: Preguntar "Tengo miedo de invertir" -> Debe recuperar docs de `soft_skill` Y `script`.
3.  **Monitorización**: Revisar los logs de `vector_store.py` (ya implementados) para confirmar que el filtro `MatchAny` se está construyendo correctamente.

***

### Resumen Técnico

*   **No se requieren cambios estructurales** en `vector_store.py` (la lógica `MatchAny` ya es correcta).
*   **Foco principal**: Ajuste fino de la lógica de decisión en `nodes.py` y calidad de los datos (metadatos) en la base de conocimientos.

