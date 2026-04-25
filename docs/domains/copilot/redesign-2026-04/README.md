# Copilot Redesign 2026-04 — "Claude Code de Marketing"

Plan de refactor del módulo `copilot/` para llegar a calidad de respuesta y arquitectura nivel Claude Code, con foco en **alta cohesión y mínimo acoplamiento**.

> **Estado:** plan aprobado, F0 lista para ejecutar.
> **Owner:** Chris (alpacapurpura).
> **Fecha inicio plan:** 2026-04-25.
> **Branch único:** `development` (ver `.claude/rules/parallel-safety.md`).

---

## Cómo se usa esta carpeta

Cada fase se ejecuta en **una conversación nueva** de Claude Code.

1. Abrís nueva conversación.
2. Pegás el prompt que vive en `prompts/F#-start.md`.
3. La conversación lee `03-phase-protocol.md` y la fase específica `phases/F#-*.md`.
4. Ejecuta la fase respetando el protocolo (research → plan → execute → quality gates → learnings → exit prompt).
5. Antes de cerrar, deposita su informe en `learnings/F#-*.md` y genera el `prompts/F{#+1}-start.md` para la siguiente fase.

Cada fase **siempre**:

- Releé contexto + objetivo + lo-que-no-se-toca antes de escribir código.
- Hace pasada de research fresco (web + Tessl/context7) — no asume que lo que sabe es lo último.
- Entrega valor independiente al usuario o al dev.
- No rompe lo que ya funciona.
- Documenta aprendizajes para que la próxima fase arranque más inteligente.

---

## Estructura

```
redesign-2026-04/
├── README.md                       # este archivo
├── 00-vision-and-non-goals.md      # qué queremos lograr + lista exhaustiva de lo que NO se toca
├── 01-master-plan.md               # 11 fases, DAG dependencias, métricas éxito
├── 02-architecture-target.md       # topología final detallada
├── 03-phase-protocol.md            # protocolo obligatorio que sigue cada fase
├── phases/
│   ├── F0-foundation-cleanup.md
│   ├── F1-provider-pattern.md
│   ├── F2-deep-agents-harness.md
│   ├── F3-brand-summary-lighthouse.md
│   ├── F4-url-contextual-scratchpad.md
│   ├── F5-ask-tenant-data.md
│   ├── F6-workflow-unification.md
│   ├── F7-channel-formatter.md
│   ├── F8-routing-cost-optim.md
│   ├── F9-quality-observability.md
│   └── F10-marketing-kb.md
├── learnings/
│   ├── _template.md                # plantilla
│   └── F#-*.md                     # cada fase deposita su informe acá al cerrar
└── prompts/
    ├── _template.md                # plantilla del starter prompt
    ├── F0-start.md                 # listo para pegar en nueva conversación
    └── F#-start.md                 # cada fase genera el siguiente al cerrar
```

---

## DAG de fases

```
F0 ──► F1 ──► F2 ──┬──► F4 ──┐
       │           │         │
       │           └──► F3 ──┼──► F5 ──┐
       │                     │         │
       │                F6 ──┤         ├──► F8 ──► F9 ──► F10
       │                     │         │
       │                F7 ──┘         │
       │                               │
       └─── (golden tests live siempre)
```

- F0 + F1 son secuenciales bloqueantes.
- F2/F3/F6/F7 paralelizables tras F1.
- F4 depende de F2 (subagents), F3 (brand summary).
- F5 depende de F1 (repos del provider) y F2 (subagents).
- F8/F9/F10 son cierre.

Ver detalle en `01-master-plan.md`.

---

## Reglas no negociables

1. **No romper lo que funciona.** Lista exhaustiva en `00-vision-and-non-goals.md` §3.
2. **Copilot es transversal.** Si modifico otro módulo (brand, offer, etc.), debe seguir funcionando standalone. Tests del módulo afectado siempre verdes antes de cerrar fase.
3. **Native-first.** Lint/tests/type-check WSL nativo, nunca `docker exec`. Migraciones idempotentes.
4. **Cada fase es atómica.** Mergeable a `development` independientemente. Si rompe, se revierte sin dependencia inversa.
5. **Documentar antes de cerrar.** Sin `learnings/F#-*.md` la fase no está terminada.
