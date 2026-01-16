# Documentación Técnica: Pipeline de Ingesta y Recuperación RAG

Este documento detalla la arquitectura de ingestión y recuperación de conocimiento (RAG) implementada en **Visionarias Brain**. El sistema utiliza una combinación de estrategias de vanguardia (State-of-the-Art) para maximizar la precisión de búsqueda y la calidad de respuesta del LLM.

## Resumen de Estrategias

El pipeline integra tres patrones arquitectónicos principales para resolver el compromiso clásico entre *búsqueda precisa* (que requiere fragmentos pequeños) y *generación coherente* (que requiere contexto amplio).

1.  **Hybrid Semantic Chunking**: Fragmentación inteligente basada en cambios de tema.
2.  **Small-to-Big Retrieval (Parent Document Retrieval)**: Búsqueda sobre índices pequeños, recuperación de contextos grandes.
3.  **Contextual Retrieval (Anthropic)**: Enriquecimiento semántico de fragmentos mediante LLM.

---

## 1. Pipeline de Ingesta (`KnowledgeService`)

Ubicación: `src/services/knowledge_service.py`

El proceso de ingesta transforma documentos crudos (PDF, TXT) en vectores altamente enriquecidos.

### Paso 1: Fragmentación Semántica Híbrida (Parent Blocks)
En lugar de cortar el texto arbitrariamente por número de caracteres, utilizamos un **Semantic Chunker** que analiza la similitud de embeddings entre oraciones consecutivas para detectar cambios naturales de tema.

*   **Objetivo**: Crear "Bloques Padres" que contengan una idea completa y coherente.
*   **Implementación**:
    *   **Primaria**: `SemanticChunker` (Percentil 90).
    *   **Seguridad**: Si un bloque semántico excede los 2000 caracteres (límite físico), se aplica recursivamente un `RecursiveCharacterTextSplitter` para dividirlo.
*   **Referencia**: *Chen et al. (2023) - "Dense X Retrieval: What Retrieval Granularity Should We Use?"* (Propone que la unidad ideal de recuperación es una proposición o hecho atómico, no una longitud arbitraria).

```python
# src/services/knowledge_service.py

# 1.1 Try Semantic Split
embeddings = self.llm_service.get_embedding_model()
semantic_splitter = SemanticChunker(embeddings=embeddings, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)
semantic_parents = semantic_splitter.create_documents([full_text])

# 1.2 Safety Check
safety_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
# ... lógica de subdivisión si > 2000 chars ...
```

### Paso 2: Small-to-Big Splitting (Child Blocks)
Cada "Bloque Padre" se subdivide en fragmentos más pequeños llamados "Hijos" (Child Chunks) de aproximadamente 300 caracteres.

*   **Objetivo**: Generar vectores de alta densidad semántica para la búsqueda. Los fragmentos pequeños son más fáciles de recuperar con precisión vectorial (cosine similarity).
*   **Referencia**: *Liu et al. (2023) - "Lost in the Middle: How Language Models Use Long Contexts"* (Fundamenta la necesidad de separar la unidad de búsqueda de la unidad de lectura).

```python
# 2. Child Split
child_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
child_docs = child_splitter.split_documents([p_doc])
```

### Paso 3: Contextual Retrieval (Estilo Anthropic)
Este es el paso de enriquecimiento crítico. A cada "Bloque Hijo" se le inyecta un contexto explicativo generado por un LLM.

*   **Problema**: Un fragmento de 300 caracteres como "La garantía es de 30 días" es ambiguo por sí solo.
*   **Solución**: Usamos el **Bloque Padre** completo como fuente para pedirle al LLM que explique de qué trata ese fragmento específico.
*   **Prompt**: *"Give a short, specific context that situates this specific chunk within the provided document section..."*
*   **Resultado**: El texto a vectorizar se convierte en: `[Contexto Explicativo] + [Texto Original del Hijo]`.
*   **Referencia**: *Anthropic - "Contextual Retrieval" (Sept 2024)* (Demuestra una reducción del 49% en fallos de recuperación al inyectar contexto local).

```python
# src/services/knowledge_service.py

prompt_context = f"""
<document_context>{p_content}</document_context>
<chunk_to_explain>{chunk.page_content}</chunk_to_explain>
TASK: Give a short, specific context...
"""
specific_context = self.llm_service.generate_response(...)
enriched_content = f"{specific_context}\n\n{chunk.page_content}"
```

### Paso 4: Indexación Vectorial
Finalmente, se guarda el vector en Qdrant con metadatos enriquecidos:
*   **Vector**: Embedding de `enriched_content`.
*   **Payload (Metadata)**:
    *   `parent_id`: ID único del bloque padre.
    *   `parent_content`: El texto completo del bloque padre (para recuperación).
    *   `strategy`: "small_to_big_contextual".

---

## 2. Pipeline de Recuperación (`vector_store`)

Ubicación: `src/services/vector_store.py`

La recuperación cierra el ciclo de la estrategia Small-to-Big.

### Paso 1: Búsqueda Vectorial Híbrida
Se realiza una búsqueda estándar en Qdrant (Dense + Sparse opcional) para encontrar los vectores "Hijos" que mejor coincidan con la consulta del usuario.

### Paso 2: Resolución Small-to-Big
Al procesar los resultados, el sistema detecta si el vector encontrado pertenece a una estrategia jerárquica.

*   **Lógica**:
    1.  Verificar `meta.get("strategy") == "small_to_big_contextual"`.
    2.  Si existe `parent_content`, **ignorar el texto del hijo** y devolver el texto del padre.
    3.  **Deduplicación**: Si varios hijos apuntan al mismo padre (ej. tres oraciones consecutivas), solo se devuelve el padre una vez.
*   **Resultado**: El LLM recibe el contexto amplio y coherente (Padre) aunque la búsqueda haya sido detonada por un detalle específico (Hijo).

```python
# src/services/vector_store.py

if strategy == "small_to_big_contextual" and parent_content:
    if parent_id in seen_parents:
        continue # Deduplicación
    
    content = parent_content
    seen_parents.add(parent_id)
    source_prefix = f"[PARENT-CTX] (Source: {source})"
else:
    content = item.get("text", "")
```

---

## Referencias Bibliográficas

1.  **Contextual Retrieval**:
    *   *Anthropic Engineering Team (2024)*. "Contextual Retrieval". [Enlace](https://www.anthropic.com/news/contextual-retrieval)
    *   Propone el uso de LLMs para generar contexto específico por chunk para mejorar embeddings.

2.  **Small-to-Big (Parent Document Retrieval)**:
    *   *Liu, N. F., et al. (2023)*. "Lost in the Middle: How Language Models Use Long Contexts". [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
    *   Establece las bases para desacoplar la unidad de recuperación de la unidad de lectura.

3.  **Semantic Chunking**:
    *   *Chen, T., et al. (2023)*. "Dense X Retrieval: What Retrieval Granularity Should We Use?". [arXiv:2312.06648](https://arxiv.org/abs/2312.06648)
    *   Analiza el impacto de la granularidad de segmentación en la eficacia de recuperación densa.
