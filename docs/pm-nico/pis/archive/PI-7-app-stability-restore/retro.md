# Retro — PI-7-app-stability-restore

## Meta

| Campo | Valor |
|---|---|
| PI | PI-7-app-stability-restore |
| Tipo | mini-PI hotfix cascade recovery |
| Inicio | 2026-05-01 |
| Cierre | 2026-05-01 (mismo día — hotfix scope) |
| Sprints | 1 (S1-cascade-bugs-fix) |
| PRs | 1 (PR-1-cascade-bugs-recovery) |
| Outcome | ✅ Métrica única éxito CUMPLIDA |

## Outcome alcanzado

**Sales agent restaurado functional end-to-end.** Bot Telegram (`@visionarias_bot`) responde correctamente con voice-tenant Visionarias. Cascade bugs #7 (brand_data_adapter PersonalityProfileModel.model_dump) + #9 (LiteLLM container exited 127) resueltos.

Smoke real Chris-mediated 2026-05-01 16:09 UTC:
- Chris: "Hola, quiero saber el precio"
- Bot: "Tenemos dos opciones: el Programa de Propósito a Prosperidad (grupal en vivo) y las sesiones Diseña tu 2026 (1:1). ¿Cuál se ajusta más a lo que buscas?"
- DB verify: `turn_end status='ok'` (26968ms duration), 4 LLM calls (gpt-4o-mini + deepseek-reasoner)

## Hipótesis vs evidencia

### H1 — Bug #7 + #9 fix end-to-end restaura sales_agent functional
**Resultado: VALIDADA fuerte.** Single smoke turn validó pipeline completo. No N+1 cascade descubierto.

### H2 — Single sprint con 2 PRs paralelos surface distinta es scope right-sized
**Resultado: REVISADA.** Architect dictaminó SPLIT: builder Sonnet para Bug #7 + PM ad-hoc Bug #9 (no requiere CONTRACT formal porque cero código). Single sprint OK pero PR cohesivo dividido en lugar de 2 PRs paralelos.

## Decisiones registradas

5 decisiones en `decisions.md`. Highlights:
- D-1 SPLIT scope cuando una surface no requiere code → PM ad-hoc
- D-3 Multi-causa fix Bug #9 (env propagation + memory) — architect missed ambas
- D-4 cost_usd=0 deuda separada NO bloqueante

## Lessons learned (críticas)

### Process

1. **Architect Opus puede missear root causes infra cuando solo usa `docker inspect`.** Architect propuso "WSL2 stale bind-mount" sin correr `docker logs` ni `docker events`. PM (yo) re-diagnose runtime reveló causas reales (ValueError startup + OOM SIGKILL exit 137). → Process improvement: fortalecer template architect prompt para forzar `docker logs <container>` cuando container exited.

2. **CONTEXT-BRIEF.md (Haiku) faithfulness=partial debe disparar architect re-scan.** Brief flag fue ignorado downstream. → Reforzar BLOQUE FIJO Path B en `01-architect-start.md` para re-run greps cuando partial.

3. **PR scope decision dinámico mid-flight es válido.** SPLIT cross-surface a builder + PM ad-hoc cuando una surface es trivial (restart + .env) evitó overhead CONTRACT formal. Pattern aplicable a futuros bugs cascade.

4. **Smoke real Chris-mediated > synthetic test post-fix.** Pipeline complejo (webhook → buffer → debounce → typing → semantic → LLM → response → trace persist) — único smoke real captura bugs cross-layer que synthetic no detectaría.

### Technical

5. **`docker-compose.yml environment:` propaga EXPLICITAMENTE.** Var en `.env` no llega al container si NO listada en service. Bug pattern recurrente.

6. **OOM SIGKILL exit 137 silent en logs app.** Workers child mueren sin Python traceback porque kernel SIGKILL es brutal. Solo `docker events --filter container=X | grep die` revela exit code real.

7. **Memory paridad cross-services es heurística válida.** brain=1536M sin OOM → litellm 1536M también safe. Replicar peer pattern elimina guessing.

8. **Cascade discovery post-observability.** PI-1.1 PR-2 shipped traces persistentes → emergencia visibilidad de bugs ocultos pre-existentes (#7 + #9 silentes hasta tener traces). Patrón confirmado: post-observability mejora siempre vale smoke profundo.

## Deudas técnicas (NO bloquean PI-7)

| # | Deuda | Severidad | Tracking |
|---|---|---|---|
| 1 | `cost_usd=0` pricing resolution falla provider mapping (deepseek tagged openai) | MED | Backlog PR follow-up sales_agent observability |
| 2 | `BrandDataAdapter` sin try/except graceful-degradation fallback (Iron Rule) | LOW | Backlog PR follow-up brand application |
| 3 | LiteLLM healthcheck CMD `curl` no existe en imagen Chainguard wolfi-base | LOW | Backlog PR follow-up infra |
| 4 | Telegram Web typing indicator inconsistente vs apps nativas (NO bug nuestro) | INFO | Sin acción — cliente issue |

## Métricas PI-7

| Métrica | Valor |
|---|---|
| Sprints | 1 (S1) |
| PRs | 1 (PR-1) |
| Builders | 1 Sonnet (Bug #7) + PM ad-hoc (Bug #9) |
| Auditors | 1 PASS iter=1 (sin fix loop) |
| Files touched | 5 (1 src + 1 test + docker-compose + .env.example + .env local) |
| LOC delta | +17/-6 |
| Commits PR | 4 (claim + Bug #7 fix + REVIEW + Bug #9 infra) |
| Duration PI total | <4 horas (mismo día start-finish) |

## Forward-compat con próximo PI

- Sales_agent stack functional baseline confirmed → PI siguiente puede asumir LLM functional
- Pricing resolution provider mapping sigue roto → próximo PR cost-tracking debe incluir
- Patrón ORM→DTO via `model_validate(orm)` aplicable a otros adapters cross-modules

## Próximo paso

Chris explícito: si más bugs descubre → **abrirá nuevo PI dedicado a pruebas E2E pre-pase-producción**. Mientras, PIs activos paralelos disponibles (PI-3 sales improvement, PI-4 brand maintenance, PI-5 copilot multicanal S3 HITL).
