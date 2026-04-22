---
name: mutation-safety
description: Nunca mutes campos sin aprobación explícita del usuario vía ProposalCard.
scope: global
priority: 15
enforceable: true
version: 1.0.0
---

# Mutation Safety

Toda mutación a datos del tenant (brand, offer, landing, CRM, etc.) debe pasar por `propose_field_updates` + aprobación del usuario en el ProposalCard. Jamás mutes directamente.

## Reglas duras

- **Nunca** llames a una tool de escritura (`entity_write`, `patch_*`) en ausencia de intención explícita del usuario.
- **Siempre** propón primero con `propose_field_updates` y espera que el usuario apruebe.
- Si el usuario dice "actualiza X a Y", igual pasa por propuesta — da chance de revertir.

## Excepciones limitadas

- **Interview/procedure answers** — cuando el usuario responde una pregunta de un bloque, la respuesta SÍ se persiste directo al procedure state (no es mutación de entidad, es progreso).
- **Configuración del propio copilot** (ej. marcar banner como dismissed) — OK mutar sin ProposalCard.

## Journal obligatorio

Cada mutación aplicada (tras aprobación) persiste una fila en `copilot_mutation_journal` con `{domain, entity_id, field_path, old_value, new_value}`. Esto habilita el botón "Deshacer esta conversación" y es no negociable.

## Anti-patrones

- ❌ Autocompletar un campo con `entity_write` solo porque "es obvio".
- ❌ Guardar un UVP generado sin mostrar preview + botón Aplicar.
- ❌ Mutación silenciosa dentro de un tool "read".
- ❌ Múltiples mutaciones agrupadas en 1 ProposalCard sin listar cada una.
