# Spanish Text (UI user-facing)

Aplica: componentes React, schemas form-runtime (labels/hints/placeholders), catálogos BE user-facing, DTOs con mensajes, prompts LLM output user, emails, notificaciones.
NO aplica: logs internos, errors técnicos, comentarios, variables, tests sin UI string.

## Regla 1 — Ortografía
Tildes + ñ + apertura `¿`/`¡`. Ej: días, Campaña, Inversión, Conversión, Configuración, Atracción, Nutrición, Adopción, Expansión, activación, adquisición, retención, ubicación.

## Regla 2 — Español LatAm neutro (sin voseo)
Tuteo (`tú`). PROHIBIDO voseo (`vos/sos/tenés/podés/mirá/dejá`) + léxico marcado (`laburo/quilombo/pibe/dale/che/bárbaro/fijate`). Nicolify vende Latam — voseo excluye MX/CO/PE/CL/EC.

**Glosario top voseo → neutro** (extendido en `references/spanish-glossary.md`):

| Voseo | Neutro |
|---|---|
| vos / sos / tenés / podés / querés | tú / eres / tienes / puedes / quieres |
| mirá / dejá / poné / usá / hacé | mira / deja / pon / usa / haz |
| elegí / agregá / configurá / revisá | elige / agrega / configura / revisa |
| guardá / abrí / volvé / cambiá | guarda / abre / vuelve / cambia |
| dale (imperativo) | asígnale / ponle / define |

## Checklist pre-commit
1. Imperativo voseado (`-ás/-és/-ís`)? → tuteo
2. Léxico regional? → neutro
3. Tildes/eñes/¿¡?

## Excepción sales_agent
Output del sales_agent respeta voz tenant (puede tener voseo si tenant es AR). Ver `sales-agent-expert` skill.
