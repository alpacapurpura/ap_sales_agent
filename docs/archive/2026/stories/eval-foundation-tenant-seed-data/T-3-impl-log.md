# T-3 Impl Log — Drafts iniciales 5 tenants seed YAMLs + READMEs

**Story:** eval-foundation-tenant-seed-data
**Ticket:** T-3 (3 of 4)
**Builder:** claude-sonnet (builder-backend) — 1 invocación
**State:** pushed
**Decisions honored:** AD1-AD8 (arch); Q1-Q3, Q6-Q8 (spec ratified)

## Files created (35)

| Tenant | Dialect | L0 | Files |
|---|---|---|---|
| tenant_coach_lat | es-PE | ✅ | brand.yaml, personality_profile.yaml, offer_ladder.yaml, pricing.yaml, buyer_personas.yaml, communication_assets.yaml, README.md |
| tenant_medicina_estetica | es-MX | ✅ | idem |
| tenant_clinica_dental | es-CO | ✅ | idem |
| tenant_agencia_growth_video | es-AR | ❌ | idem (★ magic comment `# voseo-allowed` en personality_profile.yaml) |
| tenant_agencia_automatizacion_ia | es-419 | ❌ | idem |

## Decisions in content

- **Currency PEN single-currency** los 5 tenants (Q3 ratified).
- **Buyer personas count = 3 EXACTO** per tenant (2 base + 1 adversarial-edge per Q8).
- **Dialect codes ratificados:** es-PE / es-MX / es-CO / es-AR / es-419.
- **A4+A5 SIN L0:** offer_ladder empieza en L1 ($), `has_lead_magnet=False` esperado, structlog warning `offer_ladder_missing_lead_magnet` validated.
- **A1+A2+A3 CON L0:** lead magnet level 0 explícito (PDF gratis / consulta evaluación gratis / primera consulta gratis).
- **Voseo legítimo solo A4** (es-AR) con magic comment top-of-file. Tuteo en A1/A2/A3/A5.
- **PII synthetic only:** `@example.com` emails + `+99 0 / +99 9` phone prefixes (whitelisted via `.eval-whitelist`).
- **URLs aggregate:** `visionarias.lat` real (whitelisted) + IG handles sintéticos plausibles.

## Iteration log

| iter | action | result |
|---|---|---|
| 1 | Read TenantContext + test_loader + test_schema_alignment to lock schema expectations | OK — fields known |
| 2 | Drafted 5 tenants × 7 files (35 total) | created |
| 3 | Run loader + realism + schema_alignment + pii_scanner tests | 79/79 GREEN (loader 22/22, realism 30/30, schema 16/16, dialect 4/4, pii 7/7) |
| 4 | Run pre-commit hook tests | 13/13 GREEN |
| 5 | Run arch fitness | 827/827 GREEN |
| 6 | Builder agent terminated mid-flow before staging/commit. Orchestrator recovery: gate-runner re-validate + manual stage-by-name + commit. | recovered |

## Tests output (gate-runner verbatim summary)

```
ruff check tests/fixtures/eval/tenants/ scripts/scan_seed_pii.py: All checks passed
ruff format --check ...: 9 files already formatted
pytest tests/fixtures/eval/tenants/: 79/79 PASS
  - test_pii_scanner: 7/7 PASS
  - test_dialect_catalog: 4/4 PASS
  - test_realism_smoke: 30/30 PASS
  - test_loader: 22/22 PASS
  - test_schema_alignment: 16/16 PASS
pytest tests/scripts/test_pre_commit_hook.py: 13/13 PASS
pytest tests/architecture/: 827/827 PASS
```

## Files in scope (no escape)

- ✅ `backend/tests/fixtures/eval/tenants/tenant_*/` (35 NEW)
- ✅ `06-tickets.yaml` + `checkpoint.md` + impl-log + result (tracking)
- ❌ Cero tocó `backend/src/`, `frontend/src/`, `backend/alembic/`, otros stories
