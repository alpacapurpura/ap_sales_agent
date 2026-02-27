# Implementación de "Show, Don't Tell" (Onboarding de Estilo)

Esta implementación transformará el onboarding actual en una experiencia de "Muestra, no digas", permitiendo al usuario subir su historial de chat para que el agente adopte su estilo automáticamente.

## 1. Arquitectura Backend (LangGraph & Metaprompting)

Crearemos un nuevo módulo de extracción de estilo que se ejecuta una sola vez durante el onboarding.

### A. Nuevo Módulo: `src/core/onboarding/style_extractor.py`
Este módulo contendrá la lógica del "Agente Extractor" (Metaprompting).
- **Entrada:** Texto crudo (chats de WhatsApp/Email) o Archivos.
- **Proceso:**
  1. **Análisis (Metaprompt):** Usaremos un prompt analítico (inspirado en el paper "Metaprompting") para diseccionar el texto.
  2. **Extracción Estructurada:** Generará un JSON con:
     - `tone` (ej: "Empático pero directo")
     - `signature_phrases` (ej: ["Dale con todo", "Genial"])
     - `emoji_density` (ej: "High", "End-of-sentence only")
     - `response_structure` (ej: "Short paragraphs, bullet points")
  3. **Generación de System Instruction:** Convertirá ese análisis en un bloque de texto de instrucción en segunda persona ("Tú escribes usando frases cortas...").

### B. Persistencia
- Actualizaremos el modelo `User` (o `Business`) en la base de datos para almacenar el `style_profile` (JSON) y el `custom_system_instruction` (Text).
- **Vector Store (Qdrant):** Indexaremos los chats subidos con metadatos `type="style_example"` para habilitar el **Dynamic Few-Shot Injection** (RAG Estilístico).

### C. Integración con el Agente de Ventas
Modificaremos `src/core/prompts/templates/sales_system.j2` para inyectar dinámicamente:
```jinja2
{% if user_style.instruction %}
---
🎭 TU PERSONALIDAD (CLONADA DEL USUARIO):
{{ user_style.instruction }}

Tus frases típicas: {{ user_style.signature_phrases | join(', ') }}
{% endif %}

{% if few_shot_examples %}
---
EJEMPLOS DE TU ESTILO REAL (MIMETIZA ESTO):
{% for example in few_shot_examples %}
Usuario: {{ example.input }}
Tú: {{ example.output }}
{% endfor %}
{% endif %}
```

## 2. Frontend (UX "Show, Don't Tell")

Crearemos una nueva página de onboarding en `frontend/src/app/(dashboard)/onboarding/style/page.tsx`.

### A. Componentes UI
1.  **StyleUploader:**
    -   Dropzone para archivos `.txt`, `.pdf`, `.json` (WhatsApp exports).
    -   Text Area grande para "Pegar mis mejores respuestas".
2.  **StylePreview (Feedback Loop):**
    -   Una vez analizado, mostrará una "Tarjeta de Persona" con el tono detectado.
    -   **Simulador de Chat:** Un mini-chat donde el usuario puede probar su "Clon" inmediatamente y aprobarlo.

### B. Conexión API
-   Nuevo endpoint `POST /api/v1/onboarding/analyze-style` que recibe los datos y retorna el perfil de estilo.

## 3. Plan de Ejecución

1.  **Backend - Core:** Crear `StyleExtractor` y el prompt de análisis.
2.  **Backend - API:** Crear endpoint y actualizar modelo de DB.
3.  **Backend - Agente:** Actualizar `sales_system.j2` y `node_response_generation` para soportar estilo dinámico.
4.  **Frontend:** Implementar la UI de carga y simulación.
5.  **Verificación:** Subir un historial de chat de prueba y verificar que el agente responda usando las muletillas y el tono correcto.
