# Opportunity — {Título}

> Nodo Opportunity Solution Tree (Torres). Problema validado, antes de comprometer solución.

## Meta

| Campo | Valor |
|---|---|
| Slug | {slug-kebab} |
| Estado | hipótesis / validada / descartada / ascendió a PI |
| Outcome padre | {ej: aumentar tasa activación} |
| Fecha captura | {YYYY-MM-DD} |
| Última edición | {YYYY-MM-DD} |

## Problem statement

¿Qué dolor user observamos? Describe situación, no la solución.

> Cuando {situación}, el user {comportamiento problemático/frustración}.

## Evidencia

Cómo sabemos que es real. Mínimo 1 de:
- Quotes user (entrevistas)
- Datos cuantitativos (analytics, support tickets)
- Comportamiento observado (sesiones grabadas)
- Tendencia mercado (research/{date}-{slug}.md)

## Tamaño

¿A cuántos users afecta? Frecuencia? Severidad?

| Dimensión | Valor |
|---|---|
| Reach | {% users impactados} |
| Frecuencia | {diaria / semanal / mensual / one-time} |
| Severidad | {bloqueante / fricción alta / fricción media / cosmético} |

## Soluciones candidatas

Múltiples soluciones por opportunity (Torres). NO commitear a una primero.

| Solución | Descripción 1-frase | Score RICE | Estado |
|---|---|---|---|
| Sol A | {qué} | {n} | candidato |
| Sol B | {qué} | {n} | candidato |
| Sol C | {qué} | {n} | descartada |

## Solución elegida (si aplica)

Cuándo: post-validación. Razón: {por qué A vs B}.

## Experimentos

Antes de construir, validar con experimento barato. Plan:

| Experimento | Hipótesis | Cómo medir | Resultado |
|---|---|---|---|
| {nombre} | {si X entonces Y} | {métrica} | {pendiente / pass / fail} |

## Si asciende a PI

Cuando se decide convertir en PI:
- PI link: `pis/PI-{N}-{theme}/PI.md`
- Estado: ascendió a PI
- Razón ascensión: {1 frase}
