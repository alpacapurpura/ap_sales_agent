# Roadmap — Nicolify

> Modelo: **Now / Next / Later** (Bastow). Sin fechas falsas. Promesa = dirección, no commit.
> Owner: `/pm`. Update cada vez que un PI cierra o entra nueva oportunidad priorizada.

## Now (en discovery o ejecución)

| Item | Tipo | Estado | Link |
|---|---|---|---|
| ~~Campaigns module — Foundation + Telegram MVP~~ | PI-1 | **DONE 2026-04-30** — 5 sprints / 12 PRs shipped (S0+S1+S2+S3+S4). MVP 1 Telegram outbound end-to-end. CRM Hub Lite forward-compat → archived | [pis/archive/PI-1-campaigns-module/retro.md](pis/archive/PI-1-campaigns-module/retro.md) |
| ~~PI-1 post-mortem hotfixes (#1+#2+#4+#8)~~ | PI-1.1 | **DONE 2026-05-01** — 2 sprints / 2 PRs shipped. Bugs #1+#2+#4+#8 fixed + 5-layer anti-duplication enforcement cementada. Cascade #7+#9 descubiertos handoff PI-7 | [pis/archive/PI-1.1-pi1-post-mortem/retro.md](pis/archive/PI-1.1-pi1-post-mortem/retro.md) |
| ~~App stability restore (Bug #7 brand adapter + #9 LiteLLM)~~ | PI-7 | **DONE 2026-05-01** — single sprint S1 / 1 PR shipped. Sales_agent restored functional end-to-end (smoke Chris-mediated cumplida). Cascade bugs #7 (brand_data_adapter ORM→DTO) + #9 (LiteLLM env propagation + memory OOM) → archived | [pis/archive/PI-7-app-stability-restore/retro.md](pis/archive/PI-7-app-stability-restore/retro.md) |
| ~~Growth Studio stability (drawer + bowtie + copilot offset hotfix)~~ | **PI-8** | **DONE 2026-05-01** — 1 sprint / 1 PR shipped. DetailPanel mobile z-[60], bowtie offset fix, arch ratchet (6 KNOWN_VIOLATIONS PI-9 territory). H1+H2 confirmed. | [pis/archive/PI-8-growth-studio-stability/retro.md](pis/archive/PI-8-growth-studio-stability/retro.md) |
| Copilot multicanal — Telegram MVP | PI-5 | S2 shipped (PR-2 commit `6bad657b` 2026-05-01) | [pis/active/PI-5-copilot-multicanal-telegram/PI.md](pis/active/PI-5-copilot-multicanal-telegram/PI.md) |
| **Backend Quality Guardrails — pase-prod hardening** | **PI-11** | **active 2026-05-04 — promoted Next→Now post-failed-pase-prod 2026-05-04. S1 expanded a 3 PRs (PR-1 ext + PR-3 anti-default-flip + PR-4 update agents/skills). Bloquea cualquier `/pase-produccion` confiable.** | [pis/active/PI-11-backend-quality-guardrails/PI.md](pis/active/PI-11-backend-quality-guardrails/PI.md) |

## Maintenance (rolling, paralelo a Now — no compite cap)

> Tracks evolutivos para responder feedback usuarios en días sin encolarlos en feature PIs. Cada track corre con sprints batch cortos. Closes when Chris declares.

| Item | Tipo | Estado | Link |
|---|---|---|---|
| Brand Studio evolutive maintenance | PI-4-maintenance | active, S1 in-progress (PR-1 ready) | [pis/active/PI-4-brand-evolutive-maintenance/PI.md](pis/active/PI-4-brand-evolutive-maintenance/PI.md) |

## Next (priorizado, no iniciado)

| Item | Tipo | Bloqueado por | Link |
|---|---|---|---|
| **Growth Studio architecture homologation** (registries SSoT + StageDispatcher + actions/schemas/tiers/) | **PI-9** | **desbloqueado 2026-05-01** — PI-8 shipped. Requiere Opus (architect). | [pis/active/PI-9-growth-studio-architecture/PI.md](pis/active/PI-9-growth-studio-architecture/PI.md) |
| Sales agent improvement | PI-3-sales | desplazado de Now por priorización Growth Studio (Chris 2026-05-01) — discovery, no execution-ready | [pis/active/PI-3-sales-agent-improvement/PI.md](pis/active/PI-3-sales-agent-improvement/PI.md) |
| Campaigns multi-canal (ManyChat WA + EMAIL_DRIP + commercial_director subagent) | PI-6 (placeholder) | post PI-7 + manual gate Chris staging PI-1 | _placeholder_ |
| CRM Hub completo + Segment Builder Visual + Cards copilot CRM | (placeholder) | PI-1 manual gate Chris + telemetría | _placeholder_ |

## Later (capturado, sin priorizar)

| Item | Tipo | Razón Later | Link contexto |
|---|---|---|---|
| **Growth Studio UX homologation (rediseño visual + decisión drawer-vs-route)** | **PI-10** | bloqueado por PI-9 ship | [pis/active/PI-10-growth-studio-ux-homologation/PI.md](pis/active/PI-10-growth-studio-ux-homologation/PI.md) |
| Event campaigns (webinar/launch) + CRM Hub Frontend + Retargeting Meta Ads | PI-3-campaigns (placeholder) | Bloqueado por PI-2 multi-canal | [opportunities/event-campaign-orchestration.md](opportunities/event-campaign-orchestration.md), [retargeting-meta-ads.md](opportunities/retargeting-meta-ads.md) |
| Web Push (OneSignal) + Referral / Afiliados | PI-4-campaigns (placeholder) | Tier 2 demanda no validada | [docs/pm/campaigns/03-otros-tipos/research.md] |
| AI Voice follow-up (Vapi) | TBD | Cultural risk LATAM, opt-in only | [docs/pm/campaigns/03-otros-tipos/research.md] |
| TikTok DM automation | parte de PI-2/3 | Validar # tenants TikTok Business | [opportunities/tiktok-dm-automation.md](opportunities/tiktok-dm-automation.md) |

## Done (PIs cerrados)

| PI | Cierre | Outcome | Retro |
|---|---|---|---|
| PI-1-campaigns-module | 2026-04-30 | Sistema Campañas end-to-end MVP 1 Telegram. 5 sprints / 12 PRs (S0 foundation + S1 dominio + S2 orchestrator + S3 Telegram outbound + S4 CRM Hub Lite). Forward-compat invariantes ratchet (PI-3 expand sin reescribir). 4 hipótesis validadas (H1+H3+H4 strong). 75 decisiones documentadas. Cero refactor cross-sprint. Manual gate Chris staging pendiente. | [pis/archive/PI-1-campaigns-module/retro.md](pis/archive/PI-1-campaigns-module/retro.md) |
| PI-2-copilot-improvement | 2026-04-30 | LLM stack convergencia: ModelRole único SSoT + LiteLLM Proxy motor + DB registry runtime + admin UI hot-swap <60s + GrowthBook per-tenant scaffold + eval gate pre-promote + CI workflow. Cost reduction 4-15x NANO+FAST (DeepSeek V4-Flash). Allowlist arch fitness 19→0 entries. ~140 archivos surface, ~80 tests nuevos. | [pis/archive/PI-2-copilot-improvement/retro.md](pis/archive/PI-2-copilot-improvement/retro.md) |
| PI-7-app-stability-restore | 2026-05-01 | Sales_agent restored functional end-to-end. Single sprint / 1 PR. Bug #7 (brand_data_adapter ORM→DTO via PersonalityProfileDTO.model_validate) + Bug #9 (LiteLLM container OOM 768M→1536M + LITELLM_ENVIRONMENT propagation compose). Smoke Chris-mediated cumplida (turn_end ok, 4 LLM calls). Deudas separadas: cost_usd=0 pricing mapping, graceful-degradation BrandDataAdapter, healthcheck curl missing. Process learning: architect debe correr `docker logs` no solo `docker inspect`. | [pis/archive/PI-7-app-stability-restore/retro.md](pis/archive/PI-7-app-stability-restore/retro.md) |

## Reglas roadmap

1. **Now ≤ 3 PIs feature simultáneos.** Más = pierdes foco. Si entra cuarto feature, otro pasa a pause o Later.
2. **Maintenance tracks NO cuentan cap Now.** Corren paralelo. Sin cap formal, pero si crecen (≥2 sprints batch grandes simultáneos) → upgrade a feature PI.
3. **Cada item tiene puntero.** Sin items huérfanos.
4. **Movimiento explícito.** PM mueve items vía conversación con Chris. No autoriza solo.
5. **Sin fechas duras.** Solo orden + dirección. Excepción: deadline externo regulatorio (raro).
6. **PI cerrado → Done + retro.md obligatorio.** Captura aprendizaje.

## Histórico decisiones roadmap

| Fecha | Cambio | Razón |
|---|---|---|
| 2026-04-29 | Creado track **Maintenance** paralelo a Now. Primer track: PI-4-brand-evolutive-maintenance | Chris pidió responder feedback usuarios brand en días sin encolar en feature PIs ni pelear cap Now. Patrón rolling = sprint = batch items micro |
| 2026-04-30 | Abierto **PI-5-copilot-multicanal-telegram** (discovery) | Capturado en retro PI-2 como next step ("Multicanal Bloque A — Telegram bridge"). Cap Now = 3 features (PI-1 + PI-3 + PI-5) — al límite. Scope: Telegram only (WA + IG DM = futuros PIs separados) |
| 2026-04-30 | **PI-1 cerrado + archivado** post-S4 cierre. Outcome MVP 1 Telegram alcanzado. Manual gate Chris staging pendiente. PI-6 placeholder (multi-canal) sube a Now. Cap Now = 3 (PI-3 + PI-5 + PI-6 placeholder). | PI-1 5 sprints + 12 PRs shipped en 1 día Opus 4.7[1M] sprint sizing. Cero refactor confirmed strongly (H4) |
| 2026-04-30 | **PI-5 S1 shipped** (PR-1 telegram-bot-foundation commit `c1fa2909`). **S2 abierto** con PR-2-telegram-orchestrator-hookup (single surface agentic, scope L cohesivo). | Foundation Telegram cross-stack lista (webhook + linking + tool subset registry + FE settings). S2 cablea orchestrator real + memory + cache fragment para reemplazar placeholder MVP. |
| 2026-05-01 | **PI-7 cerrado + archivado** mismo día. Sales_agent restored. Cap Now feature = 2 (PI-5 + PI-8). | Mini-PI hotfix scope: 1 sprint / 1 PR / <4h start-finish. Process learnings consolidados handoff (architect docker logs requirement). Chris explícito: si más bugs detecta → abrirá nuevo PI dedicado E2E pre-pase-prod. |
| 2026-05-01 | **Creado PI-11 (Backend Quality Guardrails) en Next con alta prioridad.** Scope: fix 10+ tests fallidos + cobertura P0 (`crm`, `scheduling`) + P1 (`sales_agent`, `copilot`). Chris quiere trabajarlo con Opus luego, no ahora. | Detección durante análisis de cobertura: crm 59.3%, scheduling 59.9%, 10 tests fallidos (mix de tests desactualizados + posibles bugs reales). Decisión Chris: guardar como PI técnico transversal para atacar con Opus cuando el ciclo actual lo permita. |
| 2026-05-01 | **Abierto PI-8 (Growth Studio stability hotfix) + PI-9 (architecture homologation Next) + PI-10 (UX homologation Later) trío secuencial.** PI-3-sales-agent-improvement desplazado de Now → Next (era discovery puro, sin execution-ready). Cap Now feature = 3 (PI-5 + PI-7 + PI-8). | Chris reportó bug latente Growth Studio drawer + arquitectura no homologada con brand/offer. Architect tech sanity check (Opus read-only) verificó 3 fixes mecánicos drawer + diff arquitectónico (falta `pages/`+`actions/`+`schemas/`) + 177 components masa = 6x brand. Decisión Chris: 3 PIs granulares (estabilidad → arquitectura escalable → UX homologation) en lugar de mega-PI. Razón: cientos clientes proyectados 1 mes exigen arquitectura escalable (open-closed agregar canales sin refactor). Anti-patterns Chris-confirmados estrictos PI-8: NO tocar `metrics-dashboard/components/`, NO consolidar dual UX path, NO hardcodear "5 stages", NO crear `schemas/`/`actions/`/`pages/` en growth (PI-9 owns), NO promover 4-tier a shared, NO `strategy-canvas/` touch, NO reescribir `useCopilotOffset`, NO cambios visuales. |
| 2026-05-04 | **PI-11 promoted Next → Now con scope expandido post-failed-pase-prod 2026-05-04.** Causa raíz detectada: commit `64738354` (PR-1 Sub-E PI-2) flipeó defaults `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy. Síntomas: 25 BE failures + 2 FE failures durante deploy + polluter snapshot test no identificable en bisección. **Decisión Chris (escala 1000 clientes 1 mes):** mantener outbox `True` permanente (in-memory rompe en multi-worker); migrar tests al path nuevo; deprecar `LegacyEventBus.publish` con runtime warning. Scope expandido S1: PR-1 ext (apply 16-archivo stash + polluter hunt sin band-aid + singleton fixture exhaustivo + EventBus mocks audit + snapshot helpers outbox-aware) + PR-3 NEW (rule `.claude/rules/anti-default-flip-audit.md` + arch fitness test bloqueador) + PR-4 NEW (update agents `nicolify-architect`/`nicolify-backend`/`nicolify-backend-auditor` + `pm` skill template + `tdd-mandatory.md`). Cap Now feature: PI-5 + PI-11. PI-11 bloqueador hard de cualquier `/pase-produccion`. |
