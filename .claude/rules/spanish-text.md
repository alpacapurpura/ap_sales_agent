# Spanish Text in UI

## Regla 1 — Ortografía
Todo texto visible al usuario en español DEBE usar tildes y caracteres especiales correctos:
- á, é, í, ó, ú (tildes)
- ñ (eñe)
- ¿, ¡ (signos de apertura cuando correspondan)

Violaciones comunes:
- dias → días
- Campana/Campanas → Campaña/Campañas
- Inversion → Inversión
- Conversion → Conversión
- Proximamente → Próximamente
- Configuracion → Configuración
- Atraccion → Atracción
- Nutricion → Nutrición
- Adopcion → Adopción
- Expansion → Expansión
- Evangelizacion → Evangelización
- activacion → activación
- adquisicion → adquisición
- retencion → retención
- ubicacion → ubicación

## Regla 2 — Variedad: Español Latinoamericano Neutro

**Todo texto que la solución Nicolify muestre al usuario DEBE estar en español latinoamericano neutro.** Nicolify se vende en todo Latam (MX, CO, PE, CL, EC, UY, AR, BO, etc.) — un dejo regional excluye a los demás mercados.

**Prohibido:** voseo argentino/rioplatense en UI, copy, placeholders, hints, tooltips, modales, notificaciones, emails, prompts que generen output visible al usuario, y catálogos (archetype/preset/section labels y descriptions).

**Regla operativa:** conjugar en **tuteo** (`tú`) con imperativos estándar. No uses `vos` ni formas voseadas. Evitá léxico marcado (`laburo`, `quilombo`, `pibe`, `chabón`, `dale`, `che`, `bárbaro`, `mirá`, `fijate`).

### Glosario voseo → neutro (aplicar siempre)

| Voseo (prohibido) | Neutro (correcto) |
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
| ves | ves (OK) |
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
| linkeá / linkealo | enlaza / enlázalo (o "pon el link") |
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
| dale (imperativo) | asígnale / ponle / define (según contexto) |

### Checklist antes de commitear texto visible

1. ¿Alguna forma voseada (`-ás`, `-és`, `-ís` en imperativo)? → corregir a tuteo
2. ¿Léxico regional marcado? → reemplazar por neutro
3. ¿Tildes y eñes correctos? (Regla 1)
4. ¿Signos de apertura `¿` `¡`?

**Aplica a:** componentes React, schemas de form-runtime (labels, hints, placeholders, options), catálogos backend que emiten texto user-facing (archetype/preset/section), DTOs con mensajes, prompts de LLM cuyo output llegue al usuario, emails, notificaciones.

**NO aplica a:** logs internos, errores técnicos de developer, comentarios de código, nombres de variables, tests unitarios cuyo string no llegue al UI.
