# Spanish Text in UI

## Regla 1 — Ortografía
Texto user-facing DEBE usar tildes + caracteres especiales:
- á, é, í, ó, ú | ñ | ¿, ¡ (apertura)

Comunes:
- dias → días | Campana → Campaña | Inversion → Inversión | Conversion → Conversión | Proximamente → Próximamente | Configuracion → Configuración | Atraccion → Atracción | Nutricion → Nutrición | Adopcion → Adopción | Expansion → Expansión | Evangelizacion → Evangelización | activacion → activación | adquisicion → adquisición | retencion → retención | ubicacion → ubicación

## Regla 2 — Español Latinoamericano Neutro

Todo user-facing Nicolify DEBE estar en **español latinoamericano neutro**. Vende Latam (MX, CO, PE, CL, EC, UY, AR, BO) — dejo regional excluye otros mercados.

**Prohibido:** voseo argentino/rioplatense en UI, copy, placeholders, hints, tooltips, modales, notificaciones, emails, prompts LLM output visible, catálogos (archetype/preset/section labels/descriptions).

**Operativa:** tuteo (`tú`) + imperativos estándar. No `vos`/voseadas. Evita léxico marcado (`laburo`, `quilombo`, `pibe`, `chabón`, `dale`, `che`, `bárbaro`, `mirá`, `fijate`).

### Glosario voseo → neutro

| Voseo | Neutro |
|---|---|
| vos | tú |
| sos | eres |
| tenés | tienes |
| querés | quieres |
| podés | puedes |
| sabés | sabes |
| hacés | haces |
| venís | vienes |
| decís | dices |
| mirá | mira |
| dejá / dejalo | deja / déjalo |
| poné / ponelo | pon / ponlo |
| usá / usalo | usa / úsalo |
| hacé / hacelo | haz / hazlo |
| elegí / elegilo | elige / elígelo |
| seleccioná | selecciona |
| arrancá / empezá | empieza / comienza |
| agregá | agrega |
| configurá | configura |
| revisá | revisa |
| escribí | escribe |
| guardá | guarda |
| subí / bajá | sube / baja |
| abrí | abre |
| volvé | vuelve |
| andá | ve |
| cambiá / cambialo | cambia / cámbialo |
| ofrecés / cobrás | ofreces / cobras |
| ejecutás / acompañás | ejecutas / acompañas |
| activás / desactivás | activas / desactivas |
| linkeá / linkealo | enlaza / enlázalo |
| despublicala / reactivá | despublícala / reactiva |
| cancelala | cancélala |
| validá / considerá | valida / considera |
| formulala | formúlala |
| marcá | marca |
| referís | llamas / te refieres |
| atendés | atiendes |
| integrás | integras |
| listá | lista |
| probá | prueba |
| mostrá | muestra |
| compartí | comparte |
| contá | cuenta |
| explicá | explica |
| fijate | ten en cuenta / revisa |
| acordate | recuerda |
| dale (imperativo) | asígnale / ponle / define |

### Checklist antes commit

1. Formas voseadas (`-ás`, `-és`, `-ís` imperativo)? → tuteo
2. Léxico regional? → neutro
3. Tildes/eñes? (Regla 1)
4. Signos apertura `¿` `¡`?

**Aplica:** componentes React, schemas form-runtime (labels/hints/placeholders/options), catálogos backend user-facing (archetype/preset/section), DTOs con mensajes, prompts LLM output user, emails, notificaciones.

**NO aplica:** logs internos, errores técnicos dev, comentarios código, nombres variables, tests cuyo string no llega UI.
