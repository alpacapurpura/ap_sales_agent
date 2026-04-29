# Story Map — Backbone

> Patton method. Backbone horizontal = actividades user (orden temporal flujo). Vertical = prioridad (walking skeleton arriba, releases abajo).

## Backbone (actividades user en orden lifecycle)

```
[Onboarding]   [Capturar marca]   [Construir oferta]   [Generar assets]   [Conectar canales]   [Lanzar agente]   [Operar ventas]   [Analizar performance]   [Iterar]
```

| # | Actividad | Estado actual | Story Map detail |
|---|---|---|---|
| 1 | Onboarding | sólido | _pendiente extracción_ |
| 2 | Capturar marca (Brand Studio) | sólido | _pendiente_ |
| 3 | Construir oferta (Offer Studio) | sólido | _pendiente_ |
| 4 | Generar assets (Landing/Copy/Flyer) | parcial | _pendiente_ |
| 5 | Conectar canales (Connections) | sólido | _pendiente_ |
| 6 | Lanzar agente (Sales Agent) | en mejora (PI-3) | _pendiente_ |
| 7 | Operar ventas (Sales Studio + CRM) | parcial | _pendiente_ |
| 8 | Analizar performance (Growth Studio) | sólido | _pendiente_ |
| 9 | Iterar / Lanzar campañas | gap (PI-1 nuevo) | _pendiente_ |

## Walking skeleton (versión mínima end-to-end)

User instala Nicolify → captura marca con scraping → define 1 oferta → genera 1 landing → conecta 1 canal (IG) → activa Sales Agent → recibe leads → opera pipeline → ve performance.

**Estado walking skeleton:** ✅ Existe end-to-end. PIs activos refinan capas siguientes.

## Stories

Stories detalladas viven en `tasks/{slug}.md`. Refactorizar cuando primer PI lo requiera (no preemptivo).

## Cómo evoluciona este archivo

- PM detecta gap en capacidad → crea/actualiza story atómica en `tasks/`.
- Backbone solo agrega actividad nueva si lifecycle user cambia (raro).
- Cada story-task linkea a opportunity / PR / PI cuando se refina.
