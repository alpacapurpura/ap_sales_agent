# Propuesta de Arquitectura: Single-Collection Metadata Filtering

Esta propuesta elimina la complejidad de gestionar múltiples colecciones físicas (que fragmentan el conocimiento y complican el mantenimiento) y la reemplaza por una estrategia robusta de **Filtrado por Metadatos** dentro de una única colección unificada.

## El Problema de las Múltiples Colecciones

Actualmente, el sistema permite crear colecciones arbitrarias (`Truth_Source_Hard`, `Sales_Psychology_Soft`), lo que causa:

1. **Silos de Información**: Si el usuario pregunta algo que cruza fronteras (ej: "¿Cómo explico el precio con empatía?"), el sistema tendría que buscar en dos colecciones separadas, duplicando costos y latencia.
2. **Complejidad Operativa**: Mantener índices, configuraciones y backups de N colecciones es ineficiente.

## La Solución: Metadata Filtering Strategy

Unificaremos todo en **una sola colección** (`visionarias_knowledge_base`) y usaremos los metadatos para "virtualizar" las categorías.

### 1. Esquema de Metadatos Unificado

Cada vector tendrá estos campos obligatorios para permitir el filtrado preciso:

* `doc_category`:  Define el "tipo" de conocimiento.

  * `hard_fact` (Datos duros: Precios, Fechas)

  * `soft_skill` (Psicología: Tono, Empatía)

  * `script` (Guiones: Manejo de objeciones)

* `source_file`: Origen del documento.

* `client_id`: Multi-tenancy (ya existente).

### 2. Lógica de Recuperación (Retrieval) Inteligente

El router (`src/core/nodes.py`) decidirá **qué** filtros aplicar según la intención del usuario, en lugar de elegir **dónde** buscar.

* **Intención** **`pricing`** -> Filtra por `doc_category: "hard_fact"`.

* **Intención** **`objection`** -> Filtra por `doc_category: ["hard_fact", "script"]` (Combina datos y guiones).

* **Intención** **`general`** -> Sin filtro de categoría (Busca en todo).

## Plan de Acción

### Fase 1: Refactorización de Vector Store (`src/services/vector_store.py`)

1. **Eliminar lógica multi-colección**: Simplificar funciones para que operen sobre una única colección por defecto.
2. **Actualizar** **`search_knowledge_base`**:

   * Aceptar un parámetro `filters: Dict` en lugar de `collection_name`.

   * Construir dinámicamente los filtros de Qdrant (`models.Filter`) basándose en los metadatos pasados.

### Fase 2: Actualización del Admin (`src/admin/app.py`)

1. **Eliminar Selector de Colección**: Reemplazarlo por un selector de **"Tipo de Conocimiento"** (Categoría) que se guardará como metadata.
2. **Unificar Visualización**: La tabla de inventario mostrará todos los documentos, con una columna "Categoría" filtrable.

### Fase 3: Migración de Datos (Limpieza)

1. **Script de Migración**: Dado que estamos en desarrollo, lo más limpio es ofrecer un botón en Admin para **"Reiniciar Base de Conocimiento"** que borre las colecciones viejas y cree la nueva unificada con el esquema correcto.

### Fase 4: Integración en el Cerebro (`src/core/nodes.py`)

1. **Actualizar Nodo RAG**:

   * Modificar la llamada a `search_knowledge_base` para inyectar filtros basados en `router_outcome` o intención detectada.

***

### Beneficios

* ✅ **Simplicidad**: Un solo índice que mantener.

* ✅ **Flexibilidad**: El agente puede "mezclar" categorías en una sola búsqueda.

* ✅ **Escalabilidad**: Añadir nuevas categorías es solo poner una etiqueta nueva, no crear infraestructura.

