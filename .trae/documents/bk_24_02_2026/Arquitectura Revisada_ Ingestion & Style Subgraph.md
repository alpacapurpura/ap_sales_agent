# Arquitectura Revisada: Ingestion & Style Subgraph

Tu intuición es correcta y se alinea perfectamente con las mejores prácticas de **Sistemas de Agentes (Agentic Systems)**.

## ¿Por qué un "Agente de Limpieza"?
En arquitecturas avanzadas (SOTA 2026), no queremos ensuciar el contexto del LLM con ruido (timestamps, "mensajes eliminados", emojis repetidos 50 veces). El principio de **"Garbage In, Garbage Out"** es crítico aquí. Si el modelo analiza basura, clonará basura.

Sin embargo, en lugar de un "Agente Autónomo" (que implica un loop infinito de razonamiento), lo que necesitamos es un **Subgraph de Ingesta (Workflow)**. Es una cadena determinista de pasos inteligentes.

## Nueva Arquitectura: `style_onboarding_graph`

Implementaremos un **Grafo de LangGraph** dedicado exclusivamente al onboarding. Este grafo tendrá la responsabilidad de tomar los datos crudos y transformarlos en oro puro (Instrucciones de Sistema).

### Estructura del Grafo (Pipeline)

1.  **Nodo 1: The Janitor (Limpiador Inteligente)**
    *   **Función:** Recibe el texto crudo (txt, pdf, paste).
    *   **Lógica (LLM + Regex):**
        *   Elimina metadatos de WhatsApp (fechas, horas, "Media omitted").
        *   Filtra mensajes cortos irrelevantes ("ok", "jajaja", "👍").
        *   Anonimiza PII (Nombres, teléfonos, emails) por seguridad.
    *   **Output:** `clean_conversation_history`

2.  **Nodo 2: The Psychologist (Extractor de Estilo)**
    *   **Función:** Analiza la conversación limpia.
    *   **Lógica (Metaprompting):** Ejecuta el prompt de "Lingüista Experto" sobre el historial limpio.
    *   **Output:** `StyleProfile` (JSON con tono, muletillas, estructura).

3.  **Nodo 3: The Architect (Generador de Prompt)**
    *   **Función:** Compila el perfil en una instrucción ejecutable.
    *   **Lógica:** Transforma el JSON en un bloque de texto en segunda persona ("Tú escribes así...").
    *   **Output:** `system_instruction_block`

4.  **Nodo 4: The Simulator (Validación)**
    *   **Función:** Genera 3 ejemplos de respuesta simulada usando el nuevo estilo.
    *   **Output:** `simulation_examples` (para mostrar en el Frontend).

### Ubicación del Código
Crearemos una nueva estructura modular para mantener el orden:
```
backend/src/core/onboarding/
├── graph.py        # Definición del flujo (Janitor -> Psychologist -> Architect)
├── nodes.py        # Lógica de cada "experto"
├── state.py        # Schema (OnboardingState)
└── prompts.py      # Prompts de limpieza y análisis
```

## Plan de Implementación Actualizado

### 1. Backend: Ingestion Subgraph (LangGraph)
*   **Crear `backend/src/core/onboarding/`**: Estructura de carpetas.
*   **Implementar `nodes.py`**:
    *   `clean_data_node`: Regex + LLM ligero (GPT-4o-mini) para limpieza rápida.
    *   `analyze_style_node`: LLM potente (GPT-4o) para extracción psicológica.
    *   `generate_instruction_node`: Formateador de texto.
*   **Implementar `graph.py`**: Conectar los nodos en un `StateGraph`.

### 2. Backend: Integración de Base de Datos
*   Actualizar modelo `User` para guardar el resultado de este proceso.
*   **Vector Store:** Indexar los ejemplos limpios ("The Janitor's output") en Qdrant con metadata `type=style_example`.

### 3. Frontend: UX de "Carga y Validación"
*   **Página:** `src/app/(dashboard)/onboarding/style/page.tsx`
*   **Flujo:**
    1.  **Upload:** Usuario sube archivo o pega texto.
    2.  **Processing:** Spinner con pasos ("Limpiando...", "Analizando personalidad...", "Generando clon...").
    3.  **Preview:** Muestra: "Tu tono es: Casual y directo. Tus muletillas: 'Vale', 'Genial'. Ejemplo de respuesta: ...".
    4.  **Aprobar/Editar:** El usuario puede ajustar manualmente si el análisis falló en algo.

### 4. Integración Final (Agente de Ventas)
*   Conectar el resultado (`user.custom_system_instruction`) al prompt del agente principal (`sales_system.j2`), tal como se planeó anteriormente.

---
**Respuesta a tu duda:** SÍ, es mejor tener un "Agente" (Subgraph) de limpieza. No confíes en que el usuario suba datos limpios. Al delegar la limpieza a un nodo especializado, garantizas que el "Extractor de Estilo" trabaje con datos de alta calidad, mejorando drásticamente el resultado final.
