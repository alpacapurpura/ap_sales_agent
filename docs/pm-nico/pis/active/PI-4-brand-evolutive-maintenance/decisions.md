# PI-4 decisions log

> Append-only. Decisiones tomadas durante el PI. PM consolida desde sprints/PRs.

| Fecha | Decisión | Razón | PR |
|---|---|---|---|
| 2026-04-29 | Track maintenance rolling, no feature PI | Responde feedback usuario en días sin romper foco PI-1/2/3 | (kickoff) |
| 2026-04-29 | Cleanup copilot por dependencia brand vive DENTRO del PR brand | Cohesión, evita splitar entre PIs, mantiene blast-radius por PR | PR-1 |
| 2026-04-29 | Eliminación buyer_persona.objections + preferred_channels approved | Feedback usuario: campos no-útiles. Verificación Explore: copilot tiene `can_propose=False` (no propuestos), sales_agent NO los lee, offer.objections es campo distinto (NO afectar) | PR-1 |
| 2026-04-29 | NO backup data prod antes DROP COLUMN | `can_propose=False` ⇒ datos sólo entran via form CRUD manual; ningún consumer downstream lee fields. Comando CSV ad-hoc disponible si emergencia | PR-1 |
| 2026-04-29 | Completeness ratio: lazy recompute on next PATCH | `_PROFILE_FIELDS` baja 9→7. NO data-fix migration bulk. Side-effect aceptable (mejora UX) | PR-1 |
| 2026-04-29 | `validate_field_path` rejection: aceptar default | Pydantic `extra="ignore"` ya filtra. NO warning log en transition (sobre-eng) | PR-1 |
| 2026-04-29 | Out-of-scope: NO cleanup adicional offer/sales_agent/KB | Distinct fields verified. Respetar blast-radius PR-1 | PR-1 |
