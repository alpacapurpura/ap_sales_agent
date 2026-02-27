# Plan de Actualización: Skill `agentic-expert`

## Objetivo
Transformar el skill actual (anteriormente `agentic-auditor`) en un **`agentic-expert`** proactivo que asista en la modificación y creación de agentes. El skill debe conocer la arquitectura del proyecto, la ubicación de los archivos y las reglas de negocio críticas (relación Lead/Customer/Communication).

## Estructura del Skill
El skill se ubicará en `.trae/skills/agentic-expert/` y constará de:
1.  **`SKILL.md`**: Archivo principal con instrucciones de activación y proceso.
2.  **`references/domain-rules.md`**: (Nuevo) Reglas de dominio específicas del proyecto (Lead vs Customer, Comunicación).
3.  **`references/project-structure.md`**: (Nuevo) Mapa de carpetas y ubicación de agentes.
4.  **`references/agentic-patterns.md`**: (Existente) Patrones de diseño de agentes.
5.  **`references/software-design.md`**: (Existente) Patrones de ingeniería de software.

## Detalles de Implementación

### 1. Actualización de `SKILL.md`
-   **Frontmatter**:
    -   `name`: `agentic-expert`
    -   `description`: "Expert Agentic Engineer for Visionarias Brain. Activates when modifying, refactoring, or creating agents (LangGraph). Enforces architecture, folder structure, and domain rules (Lead/Customer/Communication)."
-   **Contenido**:
    -   Incorporar una sección **"Project Context"** que obligue a consultar `references/project-structure.md` y `references/domain-rules.md` antes de proponer cambios.
    -   Añadir un flujo de trabajo para **"Modificación de Agentes"**:
        1.  Identificar el módulo correcto.
        2.  Verificar la separación de identidad (Customer) y contexto (Lead).
        3.  Validar el flujo de comunicación (Orchestrator).

### 2. Creación de `references/domain-rules.md`
Este archivo definirá las reglas de negocio críticas:
-   **Identidad vs Venta**:
    -   `CustomerProfile` (Marketing): Fuente única de verdad para identidad (nombre, email, teléfono, IDs de canales).
    -   `Lead` (Sales): Contexto de negociación, *linkeado* al Customer, sin duplicar datos de contacto.
-   **Comunicación**:
    -   El `ChatOrchestrator` maneja la entrada/salida.
    -   Los agentes reciben un `AgentState` enriquecido, no manejan webhooks directamente.

### 3. Creación de `references/project-structure.md`
Este archivo mapeará la ubicación de los recursos:
-   **Agentes**: `backend/src/modules/*/application/agents/` (Nodos, Grafos, Prompts).
-   **Orquestadores**: `backend/src/modules/communication/application/orchestrators/`.
-   **Servicios de Dominio**: `backend/src/modules/*/application/services/`.
-   **Modelos**: `backend/src/modules/*/infrastructure/models/`.

## Pasos de Ejecución
1.  Crear `references/domain-rules.md`.
2.  Crear `references/project-structure.md`.
3.  Reescribir `SKILL.md` con la nueva lógica y referencias.
4.  Validar que el skill se active correctamente (simulado).

## Beneficios
-   **Consistencia**: El agente siempre recordará dónde deben ir los archivos.
-   **Integridad de Datos**: Se evitará la duplicidad de datos entre Lead y Customer.
-   **Autonomía**: El skill permitirá crear nuevos agentes respetando la arquitectura existente.
