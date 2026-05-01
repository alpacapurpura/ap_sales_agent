# Roadmap — Nicolify

> Modelo: **Now / Next / Later** (Bastow). Sin fechas falsas. Promesa = dirección, no commit.
> Owner: `/pm`. Update cada vez que un PI cierra o entra nueva oportunidad priorizada.

## Now (en discovery o ejecución)

| Item | Tipo | Estado | Link |
|---|---|---|---|
| ~~Campaigns module — Foundation + Telegram MVP~~ | PI-1 | **DONE 2026-04-30** — 5 sprints / 12 PRs shipped (S0+S1+S2+S3+S4). MVP 1 Telegram outbound end-to-end. CRM Hub Lite forward-compat → archived | [pis/archive/PI-1-campaigns-module/retro.md](pis/archive/PI-1-campaigns-module/retro.md) |
| ~~PI-1 post-mortem hotfixes (#1+#2+#4+#8)~~ | PI-1.1 | **DONE 2026-05-01** — 2 sprints / 2 PRs shipped. Bugs #1+#2+#4+#8 fixed + 5-layer anti-duplication enforcement cementada. Cascade #7+#9 descubiertos handoff PI-7 | [pis/archive/PI-1.1-pi1-post-mortem/retro.md](pis/archive/PI-1.1-pi1-post-mortem/retro.md) |
| **App stability restore (Bug #7 brand adapter + #9 LiteLLM)** | **PI-7** | **active 2026-05-01 — S1 ready architect spawn** | [pis/active/PI-7-app-stability-restore/PI.md](pis/active/PI-7-app-stability-restore/PI.md) |
| **Growth Studio stability (drawer + bowtie + copilot offset hotfix)** | **PI-8** | **active 2026-05-01 — S1 ready builder spawn** | [pis/active/PI-8-growth-studio-stability/PI.md](pis/active/PI-8-growth-studio-stability/PI.md) |
| Copilot multicanal — Telegram MVP | PI-5 | S2 shipped (PR-2 commit `6bad657b` 2026-05-01) | [pis/active/PI-5-copilot-multicanal-telegram/PI.md](pis/active/PI-5-copilot-multicanal-telegram/PI.md) |

## Maintenance (rolling, paralelo a Now — no compite cap)

> Tracks evolutivos para responder feedback usuarios en días sin encolarlos en feature PIs. Cada track corre con sprints batch cortos. Closes when Chris declares.

| Item | Tipo | Estado | Link |
|---|---|---|---|
| Brand Studio evolutive maintenance | PI-4-maintenance | active, S1 in-progress (PR-1 ready) | [pis/active/PI-4-brand-evolutive-maintenance/PI.md](pis/active/PI-4-brand-evolutive-maintenance/PI.md) |

## Next (priorizado, no iniciado)

| Item | Tipo | Bloqueado por | Link |
|---|---|---|---|
| **Growth Studio architecture homologation** (registries SSoT + StageDispatcher + actions/schemas/tiers/) | **PI-9** | PI-8 ship | [pis/active/PI-9-growth-studio-architecture/PI.md](pis/active/PI-9-growth-studio-architecture/PI.md) |
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
| 2026-05-01 | **Abierto PI-8 (Growth Studio stability hotfix) + PI-9 (architecture homologation Next) + PI-10 (UX homologation Later) trío secuencial.** PI-3-sales-agent-improvement desplazado de Now → Next (era discovery puro, sin execution-ready). Cap Now feature = 3 (PI-5 + PI-7 + PI-8). | Chris reportó bug latente Growth Studio drawer + arquitectura no homologada con brand/offer. Architect tech sanity check (Opus read-only) verificó 3 fixes mecánicos drawer + diff arquitectónico (falta `pages/`+`actions/`+`schemas/`) + 177 components masa = 6x brand. Decisión Chris: 3 PIs granulares (estabilidad → arquitectura escalable → UX homologation) en lugar de mega-PI. Razón: cientos clientes proyectados 1 mes exigen arquitectura escalable (open-closed agregar canales sin refactor). Anti-patterns Chris-confirmados estrictos PI-8: NO tocar `metrics-dashboard/components/`, NO consolidar dual UX path, NO hardcodear "5 stages", NO crear `schemas/`/`actions/`/`pages/` en growth (PI-9 owns), NO promover 4-tier a shared, NO `strategy-canvas/` touch, NO reescribir `useCopilotOffset`, NO cambios visuales. |
