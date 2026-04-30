# Roadmap — Nicolify

> Modelo: **Now / Next / Later** (Bastow). Sin fechas falsas. Promesa = dirección, no commit.
> Owner: `/pm`. Update cada vez que un PI cierra o entra nueva oportunidad priorizada.

## Now (en discovery o ejecución)

| Item | Tipo | Estado | Link |
|---|---|---|---|
| Campaigns module — Foundation + Telegram MVP | PI-1 | planning, S0 in-progress | [pis/active/PI-1-campaigns-module/PI.md](pis/active/PI-1-campaigns-module/PI.md) |
| ~~Copilot improvement~~ | PI-2-copilot | **DONE 2026-04-30** — 5 sprints / 12 PRs shipped (S1+S2+S3+S4+S5). LLM stack convergencia completa: ModelRole único + LiteLLM Proxy + DB registry hot-swap + GrowthBook scaffold + eval gate. Allowlist arch fitness 0. → archived | [pis/archive/PI-2-copilot-improvement/retro.md](pis/archive/PI-2-copilot-improvement/retro.md) |
| Sales agent improvement | PI-3-sales | discovery | [pis/active/PI-3-sales-agent-improvement/PI.md](pis/active/PI-3-sales-agent-improvement/PI.md) |

## Maintenance (rolling, paralelo a Now — no compite cap)

> Tracks evolutivos para responder feedback usuarios en días sin encolarlos en feature PIs. Cada track corre con sprints batch cortos. Closes when Chris declares.

| Item | Tipo | Estado | Link |
|---|---|---|---|
| Brand Studio evolutive maintenance | PI-4-maintenance | active, S1 in-progress (PR-1 ready) | [pis/active/PI-4-brand-evolutive-maintenance/PI.md](pis/active/PI-4-brand-evolutive-maintenance/PI.md) |

## Next (priorizado, no iniciado)

| Item | Tipo | Bloqueado por | Link |
|---|---|---|---|
| Campaigns multi-canal (ManyChat bridge) + Copilot Marketing Subagent + EMAIL_DRIP | PI-2-campaigns (placeholder) | PI-1 cierre | _placeholder, abrir post PI-1_ |

## Later (capturado, sin priorizar)

| Item | Tipo | Razón Later | Link contexto |
|---|---|---|---|
| Event campaigns (webinar/launch) + CRM Hub Frontend + Retargeting Meta Ads | PI-3-campaigns (placeholder) | Bloqueado por PI-2 multi-canal | [opportunities/event-campaign-orchestration.md](opportunities/event-campaign-orchestration.md), [retargeting-meta-ads.md](opportunities/retargeting-meta-ads.md) |
| Web Push (OneSignal) + Referral / Afiliados | PI-4-campaigns (placeholder) | Tier 2 demanda no validada | [docs/pm/campaigns/03-otros-tipos/research.md] |
| AI Voice follow-up (Vapi) | TBD | Cultural risk LATAM, opt-in only | [docs/pm/campaigns/03-otros-tipos/research.md] |
| TikTok DM automation | parte de PI-2/3 | Validar # tenants TikTok Business | [opportunities/tiktok-dm-automation.md](opportunities/tiktok-dm-automation.md) |

## Done (PIs cerrados)

| PI | Cierre | Outcome | Retro |
|---|---|---|---|
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
