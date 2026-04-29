# PI-{N}-{theme} — {Título}

> Program Increment. Contenedor entrega tema-coherente. Variable scope.

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-{N}-{theme} |
| Estado | discovery / planning / building / shipped / closed |
| Tema | {1 frase} |
| Owner PM | /pm |
| Inicio | {YYYY-MM-DD} |
| Cierre estimado | variable según scope |
| Cierre real | {YYYY-MM-DD} |

## Outcome esperado

¿Qué cambia para el user al cierre? Métrica cuantitativa + cualitativa.

- Cuantitativo: {ej: 50% reducción tiempo setup campaña}
- Cualitativo: {ej: user puede crear campaña conversando con copilot}

## Hipótesis

¿Qué creemos cierto que justifica este PI? Se valida o invalida con ejecución.

- Hipótesis 1: {...}
- Hipótesis 2: {...}

## Scope

### In

- {Capacidad 1}
- {Capacidad 2}

### Out

- {Capacidad NO incluida — por qué}

## PRs candidatos

| PR | Estado | Link |
|---|---|---|
| PR-1-{slug} | drafting | [prs/PR-1-{slug}.md](prs/PR-1-{slug}.md) |
| PR-2-{slug} | discovery | [prs/PR-2-{slug}.md](prs/PR-2-{slug}.md) |

## Opportunities atendidas

Links a `opportunities/*.md` que motivaron el PI:
- `opportunities/{slug}.md` — {1 frase}

## Restricciones / Riesgos

- Restricción negocio: {ej: dependencia OAuth Meta no aprobado}
- Riesgo técnico: {ej: latencia conversacional > 3s rompe UX}
- Riesgo producto: {ej: complejidad mata adopción}

## Decisiones clave

Append-only.

| Fecha | Decisión | Razón |
|---|---|---|
| {YYYY-MM-DD} | {qué} | {por qué} |

## Métricas seguimiento

¿Qué medimos durante ejecución? Antes vs. después.

| Métrica | Baseline | Target | Cierre real |
|---|---|---|---|
| {nombre} | {valor} | {valor} | {valor} |

## Cierre / Retro

Al shipped → mover a Done en roadmap, escribir `retro.md`, update `current-state/`.
