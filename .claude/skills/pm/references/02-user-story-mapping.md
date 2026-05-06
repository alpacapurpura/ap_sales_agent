# User Story Mapping (Patton)

> Jeff Patton. Visualizar producto en 2D: backbone horizontal (actividades user en orden temporal) × vertical (prioridad).

## Estructura

```
[Onboard]   [Capt marca]   [Constr oferta]   [Lanzar agente]   [Operar ventas]   [Analizar]   ← BACKBONE
   │            │              │                │                  │               │
walking ─── walking ─── walking ─── walking ─── walking ─── walking            ← walking skeleton (release 1)
skel        skel        skel        skel        skel        skel
   │            │              │                │                  │               │
[Mejora 1]  [Mejora 1]   [Mejora 1]      [Mejora 1]         [Mejora 1]      [Mejora 1]   ← release 2
   │            │              │                │                  │               │
[Polish]    [Polish]     [Polish]        [Polish]           [Polish]        [Polish]      ← release 3
```

## Reglas

1. **Backbone = orden temporal del lifecycle**, no de prioridad.
2. **Walking skeleton (release 1)** = mínimo end-to-end funcional. Si falta UNA columna, no funciona.
3. **Niveles posteriores** = profundización por columna.
4. **Stories atómicas** = una "celda". Vive en `story-map/tasks/{slug}.md`.
5. **NO confundir con Kanban.** Story map captura producto, no work-in-progress.

## Cómo usarlo en `/pm`

| Pregunta | Respuesta |
|---|---|
| ¿Esta feature es parte del walking skeleton? | Si la quitas y nada funciona end-to-end → sí. Si solo "mejora algo" → release N+1. |
| ¿Dónde insertar story nueva? | Identificá actividad backbone correcta. Vertical = ¿es crítica MVP o mejora? |
| ¿Cómo split user story? | Por dato, operación, business rule, experiencia, técnico. Ver `04-prd-template.md`. |

## Backbone Nicolify (vivo)

Ver `docs/product/story-map/backbone.md`. 9 actividades. Walking skeleton existe ya.

## Antipatterns

- ❌ Backbone con módulos técnicos (= mapa interno, no user)
- ❌ Walking skeleton "rico" (= no es skeleton)
- ❌ Stories sin actor + beneficio
- ❌ Confundir story map con product backlog

## Reference

Patton, J. (2014). *User Story Mapping*. O'Reilly.
