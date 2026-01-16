---
alwaysApply: true
description: "Estándares de Desarrollo y Calidad"
---
# Estándares de Desarrollo
La solución está 100% dockerizada. Usar perfil 'development'.

## Entorno Docker
1. Perfil: Usar docker compose --profile development up.
2. Secretos: .env.dev es la fuente de verdad.

## Estilo de Código
- Type Hints: Obligatorios (List, Optional).
- Docs: Modelos Pydantic requieren description.
- Prompts y Markdown: Evita caracteres **. Optimiza tokens.

## Workflow Agentes
1. Estado: Definir en AgentState.
2. Prompting: flag PROMPT_SOURCE em .env indica si se obtiene de base de datos o template fisico J2 en src/core/prompts/templates/.
3. Nodo: Conectar estado y prompt.
4. Tracing: Usar decorador @trace_node para observabilidad.

## Telemetría
- Logs: Trazas PostgreSQL (AgentTrace/LLMCallLog).
- Errores: Mensajes seguros al usuario, logs detallados.