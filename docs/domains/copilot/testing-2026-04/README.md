# Copilot Testing Plan 2026-04 — "Validar el Claude Code de Marketing"

Plan de testing exhaustivo para validar que el redesign 2026-04 (F0–F11) entrega la promesa funcional + experiencial al usuario final.

> **Estado:** plan aprobado, TP0 lista para ejecutar.
> **Owner:** Chris (alpacapurpura).
> **Branch único:** `development` (ver `.claude/rules/parallel-safety.md`).
> **Modelo de trabajo:** una conversación por TP, igual que el redesign.

---

## Por qué este plan

El plan F0-F11 cerró con quality gates internos (3130 tests verde, arch fitness pass, judge avg ≥3.5/5). Eso prueba que **el código no se rompe**. NO prueba que:

- El usuario perciba el copilot como "Claude Code de marketing" (UX feel).
- La latencia real bajo carga sea aceptable (target p50 ≤800ms).
- El cost per turn sea predecible (target ~$0.05).
- La calidad del output sea coherente cross-tenant + cross-canal.
- Las regresiones se detecten antes que el user las reporte.

Este plan cubre esos 5 ejes con 12 fases de testing (TP0–TP11) que mapean 1:1 a las fases del redesign más una de baseline + una de end-to-end UX.

---

## Ejes que medimos

| Eje | Cómo se mide | Target |
|---|---|---|
| **Flujo funcional** | DeepEval `ConversationCompletenessMetric` + escenarios scripted. | 100% pasos críticos completados sin "se quedó pensando" / errores silenciosos. |
| **Calidad del entregable** | DeepEval `GEval` + `CopilotJudge` (in-process) + revisión humana de muestras. | Judge avg ≥4.0/5 cross-fase (umbral interno F9 fue 3.5; subimos para validación). |
| **Tokens + costo** | DeepEval token tracking + `copilot_turn_usage` SQL probe + `copilot_routing_log`. | Cost/turn p50 ≤$0.05 chat, ≤$0.15 audit/design. |
| **Velocidad** | DeepEval latency tracking + browser TTFB via Chrome DevTools. | TTFB p50 ≤800ms, p95 ≤2000ms. |
| **UX / sensación natural** | Chrome DevTools MCP (replay flows reales) + checklist heurístico. | 8/8 heurísticas Claude Code en TP11. |

---

## Estructura

```
testing-2026-04/
├── README.md                          # este archivo
├── 00-vision-and-coverage.md          # qué cubrimos + qué NO + criterios cierre
├── 01-tooling.md                      # DeepEval + Chrome DevTools MCP + infra interna (rationale)
├── 02-test-plan.md                    # 12 fases con DAG + dependencias
├── 03-metrics-and-targets.md          # tabla cuantitativa cross-fase
├── 04-protocol.md                     # protocolo obligatorio por TP (research → exec → diagnose → fix)
├── phases/
│   ├── TP0-baseline-observability.md  # smoke test infra + dashboards + dataset baseline
│   ├── TP1-routing-tier-selection.md  # F8/F11.1
│   ├── TP2-brand-summary-lighthouse.md# F3
│   ├── TP3-url-contextual-inspirations.md  # F4
│   ├── TP4-ask-tenant-data.md         # F5
│   ├── TP5-workflows-runtime.md       # F6
│   ├── TP6-channel-formatter.md       # F7
│   ├── TP7-marketing-kb-rag.md        # F10/F11.5
│   ├── TP8-quality-eval-observability.md  # F9/F11.5
│   ├── TP9-deep-agent-planning.md     # F2
│   ├── TP10-provider-pattern.md       # F1
│   └── TP11-end-to-end-ux.md          # heurística Claude Code feel
├── scenarios/                         # YAML / JSON scenarios reutilizables cross-TP
├── results/                           # reportes per-run (commiteados en development)
└── prompts/
    └── TP-start.md                    # prompt para arrancar nueva conversación
```

---

## DAG de fases

```
TP0 (baseline) ──► TP1 (routing) ──┐
                                   ├──► TP9 (deep_agent) ──┐
                ┌─► TP2 (brand) ───┤                       │
                ├─► TP3 (URL) ─────┤                       │
                ├─► TP4 (data) ────┼──► TP10 (provider) ───┤
                ├─► TP5 (workflows)┤                       ├──► TP11 (UX e2e)
                ├─► TP6 (channels)─┤                       │
                ├─► TP7 (RAG) ─────┤                       │
                └─► TP8 (quality) ─┘                       │
                                                           │
                       ┌─────── todos alimentan ──────────►│
```

- **TP0** secuencial bloqueante (baseline + tools setup).
- **TP1–TP8** paralelizables tras TP0 — cada una toca un eje diferente del redesign.
- **TP9, TP10** son cierre técnico (validan harness + extensibilidad).
- **TP11** sintetiza todo en heurísticas user-visible.

Ver detalle en `02-test-plan.md`.

---

## Cómo se usa esta carpeta

Cada TP se ejecuta en **una conversación nueva** de Claude Code.

1. Abrís nueva conversación.
2. Pegás el prompt de `prompts/TP-start.md`, indicando qué TP corresponde.
3. La conversación lee `04-protocol.md` + la fase específica `phases/TP#-*.md`.
4. **Pre-research mandatorio** — la conversación arranca buscando best practices actualizadas para esa fase específica antes de tocar código (regla anti-deriva).
5. Ejecuta los escenarios en orden, midiendo los 5 ejes.
6. Reporta findings en `results/TP{#}-{fecha}.md`.
7. Cualquier failure → root cause + fix arquitectónico (NO parches). Si el fix excede scope, abre issue/follow-up con plan.
8. Antes de cerrar, actualiza `phases/TP#-*.md` con escenarios nuevos descubiertos durante la corrida (el plan vive).

---

## Reglas no negociables

1. **Nunca parchar.** Cada failure se diagnostica hasta root cause. Si el fix no entra en el TP actual, se documenta + plan separado.
2. **Cada TP arranca con investigación fresca** (`04-protocol.md` paso 1). Best practices cambian rápido.
3. **5 ejes obligatorios** medidos por escenario: flujo / calidad / tokens / latencia / UX. NO se cierra TP sin los 5.
4. **Native-first.** Tests/lint/eval WSL nativo. Docker solo runtime.
5. **El plan vive.** Nuevos escenarios descubiertos se commitean. Findings se commitean. La carpeta NO es write-once.
6. **Parallel-safety.** Branch único `development`. Stage por nombre.
