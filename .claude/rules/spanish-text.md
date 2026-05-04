# Spanish Text (UI user-facing)

Aplica: React components, form-runtime schemas (labels/hints/placeholders), BE catalogs user-facing, DTOs messages, prompts LLM output user, emails, notificaciones.
NO aplica: logs internos, errors técnicos, comentarios, variables, tests sin UI string.

## R1 — Ortografía
Tildes + ñ + apertura `¿`/`¡`. Ej: días, Campaña, Inversión, Conversión, Configuración, Atracción, Nutrición, Adopción, Expansión, activación, adquisición, retención, ubicación.

## R2 — Español LatAm neutro (sin voseo)

Tuteo (`tú`). PROHIBIDO voseo (`vos/sos/tenés/podés/mirá/dejá`) + léxico marcado (`laburo/quilombo/pibe/dale/che/bárbaro/fijate`). Nicolify Latam — voseo excluye MX/CO/PE/CL/EC.

**Glosario voseo→neutro:**

| Voseo | Neutro | Voseo | Neutro |
|---|---|---|---|
| vos | tú | sos | eres |
| tenés | tienes | querés | quieres |
| podés | puedes | sabés | sabes |
| hacés | haces | venís | vienes |
| decís | dices | mirá | mira |
| dejá/dejalo | deja/déjalo | poné/ponelo | pon/ponlo |
| usá/usalo | usa/úsalo | hacé/hacelo | haz/hazlo |
| elegí/elegilo | elige/elígelo | seleccioná | selecciona |
| arrancá/empezá | empieza/comienza | agregá | agrega |
| configurá | configura | revisá | revisa |
| escribí | escribe | guardá | guarda |
| subí/bajá | sube/baja | abrí | abre |
| volvé | vuelve | andá | ve |
| cambiá/cambialo | cambia/cámbialo | ofrecés/cobrás | ofreces/cobras |
| ejecutás/acompañás | ejecutas/acompañas | activás/desactivás | activas/desactivas |
| linkeá | enlaza | despublicala/reactivá | despublícala/reactiva |
| cancelala | cancélala | validá/considerá | valida/considera |
| formulala | formúlala | marcá | marca |
| referís | llamas/te refieres | atendés | atiendes |
| integrás | integras | listá | lista |
| probá | prueba | mostrá | muestra |
| compartí | comparte | contá | cuenta |
| explicá | explica | fijate | revisa/ten en cuenta |
| acordate | recuerda | dale (imperativo) | asígnale/ponle/define |

## Checklist pre-commit
1. Imperativo voseado (`-ás/-és/-ís`) → tuteo
2. Léxico regional → neutro
3. Tildes/eñes/¿¡

## Excepción sales_agent
Output sales_agent respeta voz tenant (puede tener voseo si tenant AR). Ver `sales-agent-expert`.
