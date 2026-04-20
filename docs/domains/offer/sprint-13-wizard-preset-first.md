# Sprint 13 — Wizard preset-first rehaul

**Date:** 2026-04-19
**Branch:** development
**Goal:** Convert the "nueva oferta" wizard from archetype-driven to
preset-driven. The 7th SSoT axis (OfferTypePreset, Sprint 12) was
back-office-only until now — Sprint 13 surfaces it as the primary
user-facing decision and hides archetype as an internal tag.

## What shipped

### Backend — preset-primary `create_offer`

`OfferService.create_offer` accepts `preset_id` (optional string) and
`conditional_answers` (optional `dict[str, bool]`) alongside the legacy
`archetype` kwarg. Resolution rules:

1. `preset_id` given → look up in `OFFER_TYPE_PRESET_CATALOG`. 400 if unknown.
2. Derive `archetype` from preset. Overrides any caller-supplied value
   (preset is happy path; catalog-consistent data wins over user error).
3. `resolve_preset_flags(preset_id, conditional_answers)` — if the
   resolved flags include `IS_LEAD_MAGNET`, promote `is_lead_magnet = True`
   and coerce `value_level = LEAD_MAGNET`.
4. Legacy archetype-first path still supported (unchanged) when
   `preset_id` is omitted.
5. Neither provided → 400.

DTO `ProductCreate`:
- `archetype: OfferArchetype | None` (was required)
- `preset_id: str | None`
- `conditional_answers: dict[str, bool] | None`

### Frontend — preset-first wizard flow

`CreateOfferWizard` rewritten. Dynamic step plan (useMemo) chooses
which steps run based on preset flags + launcher context:

| Step | Component | Condition |
|---|---|---|
| 1. Preset picker | `PresetPickerStep` | Always |
| 2. Value level | `ValueLevelStep` (inline) | Skipped if preset is lead magnet or launcher preselected rung |
| 3. Conditional questions | `ConditionalQuestionsStep` | Skipped if preset has 0 questions |
| 4. Name + headline | `NamePromiseStep` (inline) | Always |
| 5. Pricing | `PricingStep` (inline) | Skipped if `is_lead_magnet` |

Archetype picker + format picker removed. Users never see
"PRODUCTO/PROGRAMA/SERVICIO" — only the user-friendly preset labels
("Consulta única", "Curso grabado", "Mastermind").

### PresetPickerStep features

- Grid of 2-column cards filtered by the tenant's `business_types`
- Each card: icon + `label_es` + `description_es` + 2-3 `examples_es` chips
- Flag-driven badges: "Gratuito" (IS_LEAD_MAGNET), "Alto ticket"
  (HIGH_TICKET), "Recurrente" (RECURRING_BILLING)
- Empty state for tenants without `business_types`: invites them to
  declare in Brand Studio; still shows all presets but with a soft hint
  that the experience is better once declared

### ConditionalQuestionsStep features

- Renders each `conditional_question.question_es` with its `help_es`
- Yes/No switch per question
- Step title adapts: "Refiná tu [preset label]"
- State lives in wizard parent (`conditionalAnswers: Record<string, boolean>`)
- Auto-skipped when the selected preset has no conditional questions

### WizardResult shape

```ts
interface WizardResult {
  preset_id?: string;           // NEW — primary axis
  archetype: OfferArchetype;     // derived from preset, kept for compat
  conditional_answers?: Record<string, boolean>; // NEW
  // ... rest unchanged (name, is_lead_magnet, has_editions, headline,
  //     status, delivery_model, value_level, currency, pricing_options)
}
```

`OfferStudioDashboard.handleCreateOffer` / `handleCreateOfferWithIA`
pass `preset_id` + `conditional_answers` through the API.
`OfferSchema` (zod): `archetype` is now optional; `preset_id` +
`conditional_answers` added as optional.

## UX flow for a new tenant

1. User signs up, completes Brand Studio onboarding (declares
   `business_types` via `BusinessTypeOnboardingDialog`).
2. Lands on Offer Studio. Header now shows `BusinessTypesChipBar` with
   their declared types — "Mostrando ofertas para: Coach/Mentor · Consultor".
3. Clicks "Nueva oferta". Wizard opens.
4. Step 1 shows 4-11 preset cards filtered to their expertise (e.g. a
   COACH_MENTOR sees `coach_sesion_unica`, `coach_paquete_sesiones`,
   `coach_programa_transformacion`, `coach_mastermind`, `coach_bootcamp`,
   `coach_curso_grabado`, `coach_retreat`, `coach_vip_day`,
   `coach_challenge_gratis`, `coach_ebook_workbook`).
5. Picks one. Archetype + format are resolved silently from the catalog.
6. Steps 2-5 run as applicable (value level if not lead-magnet preset,
   conditional questions if any, name, pricing).
7. Offer is created with `preset_id` persisted. Downstream (sales-agent
   grounding, landing generator, PresetBadge on the dashboard card)
   immediately works.

## Backwards compatibility

IA pipelines and legacy API clients that still send `archetype` without
`preset_id` continue to work. The service routes them through the
legacy branch. The only change they notice is that new offers now
optionally carry `preset_id = NULL`, which the dashboard handles
gracefully (no badge renders for null presets).

## Validation

| Suite | Result |
|---|---|
| Backend arch tests | 332/332 ✅ |
| Backend offer tests | 514/514 ✅ |
| Frontend arch tests | 16/16 ✅ |
| Frontend schema tests | 97/97 ✅ |
| Frontend brand-studio tests | 91/91 ✅ |
| TypeScript | 0 errors ✅ |
| ESLint | 0 errors ✅ |

## Commits

| SHA | Piece |
|---|---|
| `b3b6f42a` | Q2 — BusinessTypes visibility (chip bar + read-only section) |
| `c6684673` | 13.B1 — backend preset-primary create_offer |
| `ecb8914b` | 13.B3 — frontend wizard rehaul (+ PresetPickerStep + ConditionalQuestionsStep) |

## Deferred to Sprint 14+

- **Per-archetype landing content builders** (mentioned in Sprint 14
  doc; still pending): right now every non-squeeze archetype still
  renders SqueezeContent as structural superset.
- **Preset editor in Offer Studio settings**: admins who want to
  customize preset defaults for their tenant currently cannot — the
  catalog is platform-global. This is deliberate for now; a Sprint 16+
  feature once we validate demand.
- **Wizard analytics**: instrument step drop-off + preset-pick
  distribution so we can tune the catalog (which presets lead to
  completed offers vs which get abandoned).
- **Preset-aware specialist prompts**: the sales-agent currently reads
  `preset_label` + `preset_flags` for grounding, but specialist prompts
  (closer, qualifier) could load preset-specific playbooks from Qdrant.

## Related docs

- `docs/domains/offer/offer-type-preset-catalog.md` — original axis design
- `docs/domains/offer/schemas-latam-refinement.md` — Task B schemas
- `docs/domains/offer/sprint-14-preset-backfill-and-downstream.md` —
  backfill + sales-agent + landing gen
- `.claude/skills/offer-type-preset-expert/SKILL.md` — maintenance guide
