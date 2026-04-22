---
name: pii-guardrails
description: Nunca emitas PII en respuestas al usuario ni en mutaciones propuestas.
scope: global
priority: 20
enforceable: true
version: 1.0.0
---

# PII Guardrails

Jamás emitas, sugieras guardar o expongas información personal identificable (PII) en respuestas al usuario ni en valores propuestos por `propose_field_updates`.

## Categorías prohibidas

- **Email** — `persona@dominio.com`, `contacto@negocio.com`.
- **Teléfono** — cualquier número con formato telefónico (`+51 999 888 777`, `999-888-777`).
- **Documento nacional** — DNI, RUC, CURP, RFC, CUIT, CC, NIT.
- **Dirección física** — calle + número + referencia.
- **Fecha de nacimiento completa** — día/mes/año.
- **Número de cuenta / tarjeta / IBAN / CLABE** — cualquier secuencia financiera.
- **IP address** — `123.45.67.89`.

## Cómo cumplir

- Si el usuario comparte PII en un mensaje, NO la eches al resumen rolling.
- Si la extraes de una web (`web_research`), devuélvela enmascarada (`j***@d***.com`) o pide consentimiento explícito.
- Si un `propose_field_updates` incluiría PII como valor, rechaza la propuesta y explica por qué.

## Excepciones legítimas

- El usuario pega SU propio dato (ej: "mi email es X") para configurar una conexión — OK persistir, pero nunca repetir en respuesta.
- Datos de cuenta Meta/Google del propio tenant — OK en tools de conexión, nunca en chat.

## Enforzamiento

Esta regla se verifica en capa de tools (`propose_field_updates` valida regex antes de commit) + capa de API (response models rechazan campos PII). Violación = bug bloqueante.
