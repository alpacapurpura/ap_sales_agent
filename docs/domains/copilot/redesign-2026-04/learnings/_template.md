# Learnings — F# {Slug}

**Fecha cierre:** YYYY-MM-DD · **Modelo:** Claude X.Y · **Branch:** `development @ <hash>`

> **Regla de oro:** este doc lo va a leer una fase futura. Solo escribí lo que esa fase NECESITA saber para no repetir errores ni redescubrir contexto. Cualquier cosa derivable de `git log`, los docs base o el código actual NO va acá.
>
> Si una sección de abajo no tiene contenido relevante para esta fase, **eliminala** — mejor un doc corto y útil que uno largo con campos vacíos.

---

## Resumen 3 líneas

- Línea 1: qué se entregó (concreto, verificable).
- Línea 2: qué decisión no obvia se tomó.
- Línea 3: qué queda listo para la fase siguiente.

---

## Decisiones clave

Solo decisiones donde el camino tomado **no era el único razonable**. Para cada una: razón + alternativa descartada en una línea.

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| | | |

---

## Sorpresas / gotchas (críticos, no triviales)

Cosas que no estaban en los docs y que la próxima fase descubriría a la fuerza:

- Bug de versión específica de una lib (anotar versión exacta + síntoma).
- Comportamiento no documentado de un componente del repo.
- Test fragility pre-existente que tocó al pasar y va a tocar de nuevo.
- Discrepancia entre el plan original y la realidad del código.

Nada de "todo funcionó bien" — eso no aporta.

---

## Recomendaciones accionables para F{#+1}

Cada bullet = una acción concreta que F{#+1} debería ejecutar antes/durante su trabajo.

- Antes de empezar: correr `<comando>` para validar `<X>`.
- Al codear: usar el hook `<archivo>` que dejé listo en `<path>`.
- Si descubrís `<síntoma>`: ya lo investigué, está en `<sección>` arriba.
- Considerar ajustar el plan F{#+1} en el punto `<X>` por aprendizaje `<Y>`.

---

## Riesgos abiertos

Cosas que quedaron andando pero frágiles. Cada riesgo: qué puede romper + dónde mirar primero.

- (...)

---

## Hooks listos para próximas fases

Si dejaste código/test/config preparado para que una fase posterior lo consuma directo, listarlo acá con su path exacto y cómo activarlo.

- Path: `...` — qué hace, cómo se activa.

---

## Fuentes research útiles

Solo las que aportaron decisiones. No la lista exhaustiva de búsquedas.

- [Título](URL) — qué cambió en mi enfoque por leer esto.
- Tessl tile `tessl__X` — qué confirmé/descarté.
