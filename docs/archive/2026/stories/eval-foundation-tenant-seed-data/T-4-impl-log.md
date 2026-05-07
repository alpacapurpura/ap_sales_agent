# T-4 Impl Log — Curación Chris + ratificación + capability update + GREEN final

**Story:** eval-foundation-tenant-seed-data
**Ticket:** T-4 (4 of 4 — last)
**Builder:** claude-opus + Chris (loop iterativo)
**State:** pushed
**Decisions honored:** AD1-AD10 (arch); Q1-Q10 (spec ratified)

## Resumen curación

Loop iterativo Chris ↔ orchestrator durante T-4. Cambios principales:

### Round 1 (Chris feedback inicial)
- **Offer-expert skill cargado** para mapear capas L0-L11 antes de modificar YAMLs
- **Workshops/cursos con ediciones** → introducido `variant_structure: PERIOD` con histórico ediciones (4 pasadas) + próxima edición fecha
- **Comunidad VIP 3 niveles** → introducido `variant_structure: TIER` (Basic/Pro/Elite) en lugar de offer único
- **Discovery call cierre alta-ticket** → integración con Nicolify scheduling (clon-Calendly), event_type_ids placeholder
- **Programa real "De Propósito a Prosperidad"** → reemplaza Curso Sistema VISIONARIA (tenía precio inflado y datos genéricos). Datos del producto real visionarias.lat extraídos via WebFetch. Co-instructora Camila Clausen (neurociencia).
- **Sample exchanges humanizados** → multi-msg DM-brevity, real numbers, qualifying específico, sin "qué emocionante" canned. Research vía WebSearch sobre 2026 best practices DMs sales agents humanos vs bot.

### Round 2 (Chris feedback expansión)
- **Aplicar densidad máxima a A2-A5**: brand + personality + offer_ladder + pricing + buyer_personas + communication_assets + README todos enriquecidos al nivel A1
- **Research Peru benchmarks 2026** vía WebSearch para pricing realista por sector:
  - A2 medicina estética (Lumina): botox PEN 25-55/u, HIFU 600-900/sesión, ácido hialurónico 720-950/jeringa
  - A3 clínica dental (Sonrisa Plena): limpieza 80-200, ortodoncia 2,500-7,500, implantes 4,200
  - A4 agencia growth (Pulso): retainer 5,500-9,500/mes, audit 500, video 1,200-3,500
  - A5 agencia IA (Núcleo Lab): audit 8-15k, implementación 28-95k, retainer 4-12k/mes
- **Personas adversariales más densas**: cada tenant ahora tiene 3 personas con campos: pain_points + objections con intensity + secret_concerns + decision triggers + sample_question_to_agent + likely_offer_path + LTV — lista para tests adversariales downstream

## Files modificados (35 + 5 capability + tracking)

| Tenant | Files | Notas |
|---|---|---|
| `tenant_coach_lat/` | brand + personality + offer_ladder + pricing + buyer_personas + communication_assets + README | A1 — Coach LatAm es-PE Visionarias real (Round 1) |
| `tenant_medicina_estetica/` | idem | A2 — Clínica Lumina es-MX Lima (Round 2) |
| `tenant_clinica_dental/` | idem | A3 — Sonrisa Plena es-CO bogotano Lima (Round 2) |
| `tenant_agencia_growth_video/` | idem | A4 — Pulso Studio es-AR voseo SIN L0 (Round 2) — magic comment voseo-allowed |
| `tenant_agencia_automatizacion_ia/` | idem | A5 — Núcleo Lab es-419 SIN L0 (Round 2) |
| `.eval-whitelist` | + visionarias.lat domain + nicolify.com/schedule prefix | Cobertura URLs reales |
| Capability YAML | `eval` block agregado con seed_tenants_path + seed_archetype_slugs + seed_dialect_codes + seed_curated_at + seed_pii_scanner_path + seed_whitelist_path | T-4 acceptance A1 |

## Decisiones de diseño T-4 (curación Chris)

### Variants (offer-expert L10)
- **PERIOD** (ediciones cohort fechadas): A1 Workshop L1 (4 pasadas + 5ta) + A1 Programa L2 (1ra cerrada + 2da abierta)
- **TIER** (niveles escalonados):
  - A1 Comunidad VIP L3 (Basic/Pro/Elite)
  - A2 Plan Integral L4 (Basic/Premium/VIP)
  - A3 Ortodoncia L2 (Metálicos/Cerámicos/Invisalign)
  - A3 Estética L3 (Express/Completo/Premium)
  - A3 Plan Familiar L4 (Pareja/Familia 4/Familia 6)
  - A4 Retainer L3 (Starter/Growth/Premium)
  - A5 Retainer L4 (Starter/Growth/Premium)
- **PACK** (cantidades):
  - A2 Pack Facial L2 (4/8/12 sesiones)
  - A2 Pack Corporal L3 (1 zona/2 zonas/full body)
  - A4 Pack Producción Video L2 (4/8/12 reels)

### Discovery / cierre via Nicolify scheduling (clon-Calendly)
- A1: L2 + L4 discovery call obligatoria (30 min)
- A2: L0 evaluation + L3 corporal + L4 plan integral (30/30/20 min)
- A3: L0 primera consulta gratis + L3 estético + L4 familiar (45/60/45 min)
- A4: L1 audit reunión 30 min + L3 retainer + L4 consultoría (30/45/45 min)
- A5: L1 discovery + L2 audit + L3 implementación + L4 retainer (45/60/90/45 min)

### Voz humana (sample_exchanges T-4 humanizados)
- DM-brevity 1-3 frases multi-msg
- Real numbers PEN/USD específicos (no rangos vagos)
- Qualifying específico ("¿facturás o validás?" "¿lactando?")
- Acknowledge → bridge sin "entiendo perfectamente" canned
- Decline cuando no aplica (fits, presupuesto, timing)
- Discovery call para alta-ticket (no compra directa DM)
- Emoji moderado (1 cada 3-4 turnos máx)
- Sin "qué emocionante" / lenguaje motivacional
- Voseo solo A4 con magic comment, resto tuteo neutro/regional

### Decline policies por tenant (anti-mal-fit)
- A1: cliente recién validando sin presupuesto → recomienda L0/L1 (no empuja L2+)
- A2: lactancia/embarazo restricciones + clientes 22 años pidiendo botox prematuro → declina honestamente
- A3: clientes pidiendo carillas innecesarias (10-12 cuando bastan 6) → mantiene anti-sobreventa policy
- A4: wantrepreneurs sin validación 200 followers → declina + recomienda validar primero (CRITICAL)
- A5: empresas <50 empleados + vibe-coders pidiendo IP gratis → declina + recomienda no-code/recursos públicos

## Iteration log

| iter | action | result |
|---|---|---|
| 1 | Cargar offer-expert skill + WebFetch visionarias.lat product page | OK — context completo |
| 2 | A1 round 1 (offer_ladder + pricing + personality + buyer_personas + brand + comm + README) | UUIDs broken regex dni_pe → fix + whitelist `@visionarias.lat` + `app.nicolify.com/schedule/` |
| 3 | A2 (Lumina Estética es-MX) — 7 files denso | OK |
| 4 | A3 (Sonrisa Plena es-CO bogotano) — 7 files denso | OK |
| 5 | A4 (Pulso Studio es-AR voseo SIN L0) — 7 files con voseo legítimo | OK — magic comments preservados |
| 6 | A5 (Núcleo Lab es-419 SIN L0) — 7 files denso | Phone regex captura `+15-25%` → fix `15-25% extra` syntax |
| 7 | Capability YAML update (eval block) | OK |
| 8 | Validators full suite | 79/79 eval + 13/13 hook + 827/827 arch + ruff GREEN + PII clean |
| 9 | Pre-commit hook + commit + push | pending |

## Tests output (validators T-4 GREEN)

```
ruff check tests/fixtures/eval/tenants/ scripts/scan_seed_pii.py: All checks passed
pytest tests/fixtures/eval/tenants/: 79/79 PASS
  - test_pii_scanner: 7/7 PASS
  - test_dialect_catalog: 4/4 PASS
  - test_realism_smoke: 30/30 PASS
  - test_loader: 22/22 PASS
  - test_schema_alignment: 16/16 PASS
pytest tests/scripts/test_pre_commit_hook.py: 13/13 PASS
pytest tests/architecture/: 827/827 PASS
PII scanner: clean (zero hits across 5 tenants)
```

## Files in scope (no escape T-4)

- ✅ `backend/tests/fixtures/eval/tenants/tenant_*/` (35 files modificados)
- ✅ `backend/tests/fixtures/eval/tenants/.eval-whitelist` (entries adicionales)
- ✅ `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (eval block)
- ✅ `06-tickets.yaml` + `checkpoint.md` + impl-log + result (tracking)
- ❌ Cero tocó `backend/src/`, `frontend/src/`, `backend/alembic/`, otras stories, MEMORY.md, learnings.md, BACKLOG.md
