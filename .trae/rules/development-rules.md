---
alwaysApply: true
description: "Estándares de Desarrollo y Calidad"
---
# Estándares de Desarrollo

PRIORIDAD: DESARROLLO (LOCAL)
Asumir entorno local salvo indicación explícita de PRODUCCIÓN.

## Gestión de Entornos
Sistema de doble archivo para seguridad:
1. .env.dev (Local): Configuración Docker/debug completa.
2. .env.prod (Producción): Plantilla segura sin secretos.
3. .env (Link): Symlink a .env.dev en local.

Regla: Editar .env.dev para cambios locales, nunca .env si es symlink. Mantener claves en .env.prod.

## Estilo de Código
* Type Hints: Obligatorios en todas las firmas de función (`typing.List`, `Optional`, etc.)
* Docs: Modelos Pydantic requieren campo `description` para dar contexto semántico al LLM.

## Workflow Agentes
1. Estado: Identificar qué variables cambian en `AgentState`.
2. Prompting: Crear el template `.j2` en `src/core/prompts/templates/`.
3. Nodo: Conectar estado y prompt en Python.
4. Test: Validar transiciones.

## Telemetría y Errores
* Logs: Registrar cada interacción (Input, State_Before, Action, Output, State_After) en PostgreSQL para futuro RLHF.
* Fallbacks: Si falla OpenAI o la API, responder con mensaje seguro. NUNCA exponer stack traces al usuario final.
