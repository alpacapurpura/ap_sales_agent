# Análisis: Paper "Proto-Personas" vs Tu Arquitectura Actual

He revisado a fondo tu código (`onboarding/nodes.py`, `prompts.py`, `sales_system.j2`) y lo he contrastado con el paper `2507.08594v1`.

## 1. Veredicto Directo: ¿Tu solución actual funciona o el paper es mejor?
**Tu solución actual YA implementa la filosofía del paper, y de hecho, es la forma correcta de "ahorrar tokens".**

*   **Lo que el paper propone:** No usar datos crudos en el prompt final, sino usar GenAI para crear una "Proto-Persona" (un perfil resumido) y usar *ese perfil* para guiar al agente.
*   **Lo que tú haces:** Tu nodo `Janitor` -> `Psychologist` -> `Architect` hace exactamente eso.
    *   **Ingesta:** Tomas chats crudos.
    *   **Procesamiento:** El `Psychologist` extrae un `style_profile`.
    *   **Prompt Final:** El `Architect` crea una `system_instruction` (tu Proto-Persona) que se inyecta en `sales_system.j2`.

**Conclusión de Tokens:**
No estás desperdiciando tokens enviando "50 chats pasados" al agente en vivo. Solo envías la `custom_instruction` destilada. En términos de eficiencia, **estás en el estado óptimo**.

## 2. La Oportunidad de Mejora (Calidad y Empatía)
Aunque la arquitectura es correcta, el paper menciona un hallazgo clave: **"La empatía afectiva y conductual varía significativamente si no se diseña bien"**.

Revisé tu `PSYCHOLOGIST_PROMPT` actual y se enfoca mucho en la **FORMA** (Sintaxis):
*   ✅ Emojis, Frases clave, Estructura de párrafos.
*   ❌ **Falta el FONDO (Cognición):** ¿Cómo piensa el usuario? ¿Cómo maneja objeciones emocionalmente? ¿Es agresivo o consultivo?

Si solo clonamos la forma, el agente "suena" como el usuario pero puede "pensar" como un robot genérico.

## 3. Plan de Acción
Para "implementar una mejor solución" basada en el paper, no cambiaremos la arquitectura, sino que **potenciaremos la profundidad del perfil psicológico** para capturar esa "Empatía Conductual".

### Paso 1: Actualizar `PSYCHOLOGIST_PROMPT` (`backend/src/core/onboarding/prompts.py`)
Agregaremos dimensiones cognitivas al análisis:
*   **Mecanismos de Empatía:** ¿Cómo valida los sentimientos del otro?
*   **Patrones de Persuasión:** ¿Usa lógica, emoción o autoridad?
*   **Manejo de Conflicto:** ¿Cede, negocia o se mantiene firme?

### Paso 2: Actualizar `ARCHITECT_PROMPT`
Para que traduzca estos nuevos hallazgos psicológicos en instrucciones de sistema ejecutables (ej: "Cuando el cliente dude, no uses datos, usa una historia personal").

Esta mejora no costará más tokens en tiempo de ejecución (el prompt final sigue siendo texto comprimido), pero la calidad de la "personalidad" será muy superior.
