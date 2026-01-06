---
alwaysApply: false
description: 
---
# Arquitectura: Visionarias Agent (AISALESHT)

## Filosofía Code-First
*   **No Low-Code**: Lógica 100% en Python para garantizar control, testabilidad y versionado.
*   **Determinismo**: El agente sigue una Máquina de Estados Finita (S1 $\rightarrow$ S6) definida explícitamente con `LangGraph`. No hay divagación.
*   **Separación de Capas**: 
    *   `src/core`: Lógica Cognitiva (Grafos, Nodos).
    *   `src/api`: Transporte (Webhooks, HTTP).
    *   `src/services`: Infraestructura (DB, Redis).

## Seguridad y Datos
*   **Cero Alucinaciones**: El LLM **NUNCA** calcula precios.
*   **Financial Enforcer**: Herramienta determinista obligatoria que sobrescribe cualquier número generado por el LLM con datos de la "Fuente de Verdad" (Base de Datos).
*   **RAG Contextual**: El retriever debe filtrar chunks por estado actual (ej. en `S5_Anchoring` priorizar etiquetas `hard_data` y `finance`).
