---
story_id: sales-agent-voice-fidelity-ci-gate
type: service-story
module: sales_agent
capability: sales-conversational-engine
links:
  story_yaml: "../../../../../../product/stories/sales-agent/voice-fidelity-ci-gate.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — Voice Fidelity CI Gate

## Job-To-Be-Done

**Como** owner del producto
**Quiero** que cada PR que toque `modules/sales_agent/` corra el voice fidelity grader contra los 12 goldens y bloquee el merge si el score agregado cae bajo 0.7
**Para** que regresiones de voz queden atrapadas en CI antes de llegar a producción y que clientes se quejen

## Por qué importa

Story 7 implementa el grader. Sin esta story, el grader es decoración — corre cuando alguien lo invoca manualmente, lo cual nunca pasa porque los devs se olvidan o no saben. Hacer el grader **obligatorio en CI** es lo que convierte la métrica en garantía operacional.

Es la pieza que cierra el loop del Objetivo 2 del PI: "Voice fidelity grader en CI gate". Hasta acá teníamos las partes (goldens, personas, grader). Esta story las une al pipeline de PR.

## Outcome esperado

- Nuevo job `voice-fidelity-gate` en `/test-backend` (o nuevo `/test-agentic-evals` standalone — decidir en `01-spec.md`)
- El job se dispara automáticamente cuando un PR toca:
  - `backend/src/modules/sales_agent/**`
  - `backend/src/shared/agent_observability/**` (cost tracking compartido afecta runs)
  - `backend/tests/agentic_evals/sales_agent/**`
  - `docs/specs/personas/*.yaml` o `docs/specs/rubrics/voice-fidelity.md`
- El job:
  1. Corre los 12 goldens × 3 trials con personas instrumentadas (Story 6) — usa runner Story 1 + pass^k Story 2 + budget cap Story 3
  2. Por cada output del agente, llama `grade_voice_fidelity()` (Story 7)
  3. Calcula `voice_fidelity_score_aggregate` = mediana de scores por golden
  4. Lee threshold de env var `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7`
  5. Si `aggregate < threshold` → exit non-zero → PR bloqueado
- Reporte estructurado en PR comment (vía GitHub Actions o `gh pr comment`):
  - Score agregado + verde/rojo
  - Top 3 goldens con peor score
  - Link a calibración doc para contexto
  - Si rojo: instrucciones para reproducir local
- **Modo "warning only" 1 semana**: env var `SALES_AGENT_VOICE_FIDELITY_GATE_MODE=warning` durante rollout suave. Después switch a `block` (default). Documentar en `process/learnings.md` que la decisión es deliberada
- Cache de scores por `(commit_sha, output_hash, tenant_voice_profile_hash)` — re-corridas del CI sobre mismo PR no re-pagan judge
- Test sintético: PR con cambio que rompe voz deliberadamente → gate bloquea correctamente

## Antecedentes / Contexto

- **Depende de:** Stories 1, 2, 3, 5, 6, 7 (todas las anteriores deben estar audit-passed)
- **Threshold env var:** `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` (Decision 30, ya declarada)
- **Mode env var:** `SALES_AGENT_VOICE_FIDELITY_GATE_MODE=warning|block` (esta story la introduce)
- **CI surface:** GitHub Actions workflow + posible nuevo `/test-agentic-evals` slash command para correrlo local
- **Decisión cardinal:** rollout 1 semana en warning antes de hard-block — evita bloquear devs durante calibración inicial real con producción
- **Skills:** `sales-agent-expert`, `playwright-expert` (CI patterns), `tessl__pytest-api-testing`

## Out of scope (explícito)

- Cambiar el grader implementation — eso es Story 7
- Per-tenant threshold (scope global env var)
- Notificaciones externas Slack/email — usar PR comment estándar
- Auto-merge si score muy alto (>0.95) — gate solo bloquea, no aprueba
- Backfill scoring sobre PRs históricos
- Gate corriendo en otros módulos (copilot, brand) — esta story es sales_agent only
- Cost gate (esto lo hace Story 3 separado)

## Riesgos / Asunciones

- **Riesgo:** Gate flaky bloquea PRs legítimos por variance del judge (LLM nondeterministic). **Mitigación:** Mediana en lugar de mean para aggregate (reduce outliers). Mode warning 1 semana para detectar false positives antes de hard-block. Threshold 0.7 con buffer.
- **Riesgo:** CI run lento (12 goldens × 3 trials × persona overhead × judge calls = minutos). **Mitigación:** Cache aggressive. Considerar correr solo subset (3 personas) en gate, full en nightly.
- **Riesgo:** Costo CI runs explota cuando hay muchos PRs. **Mitigación:** Story 3 budget cap aplica. Cache scores por commit_sha (re-runs gratis). Evaluar si gate corre solo en push a development o también en branch PRs.
- **Asunción:** GitHub Actions tiene secretos para LLM provider keys (Anthropic) ya configurados o se agregan en esta story.
- **Asunción:** El equipo (vos solo o futuro multi-dev) acepta que un PR puede ser bloqueado por voice drift — política operacional clara, no sorpresa.

## Próximo paso

`→ /po lee este archivo + Stories 1-7 specs/results → produce 01-spec.md Gherkin (escenarios: happy gate verde, edge mode warning report sin block, adversarial gate bypass intent + cost runaway protection, calibración trigger) + actualiza story YAML`
