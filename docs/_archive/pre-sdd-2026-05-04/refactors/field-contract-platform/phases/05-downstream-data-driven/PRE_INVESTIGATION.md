# Pre-investigación obligatoria — Fase 05

## Sección 1 — Sales-agent prompt inventory

**Q1.1** — Inventario completo de `{% if offer.X %}` blocks en
`agent_identity.j2` (y otros templates sales-agent).

```bash
grep -rn "offer\." backend/src/modules/sales_agent/.../prompts/ --include="*.j2"
find backend/src/modules/sales_agent -name "*.j2" -exec grep -l "offer\." {} +
```

Documentar cada field consumido + su lógica (condicional, default, formato).

**Q1.2** — ¿Hay fields renderizados que no tienen entry en `FieldContract`?

Si sí → tech debt: extender FieldContract en commit dedicado dentro
de Fase 05 (NO en Fase 04 — fuera scope).

## Sección 2 — Landing builders inventory

**Q2.1** — ¿Qué builders en `landing/application/services/landing_content_builders.py`
leen offer fields?

```bash
grep -rn "offer\." backend/src/modules/landing/application/services/landing_content_builders.py
```

Documentar field reads, transformations, layouts.

**Q2.2** — ¿Builder lee `pricing` JSONB legacy o top-level fields?

Lección Fase 01: builders consumen JSONB. Aterrizar al FieldContract
top-level o dejar JSONB? Decisión documentada.

## Sección 3 — Completion service

**Q3.1** — Lógica actual de `offer_completion_service.py`. Cómo calcula %?

**Q3.2** — Cómo se mapea a `is_required_semantic`?

¿Hay fields hoy considerados "required" para completion que no tienen
override `is_required_semantic=True` en el FieldContract?

## Sección 4 — Golden snapshots disponibles

**Q4.1** — ¿Existe `capture_offer_a96403b5_baseline.py` actualizado?

Sí desde Fase 00 del refactor anterior. Captura: DB state +
`agent_identity.j2` rendered + landing output. Re-ejecutar pre-fase-05
para baseline.

## Sección 5 — Tests existentes

**Q5.1** — Tests sales-agent prompt + landing builders + completion.

```bash
find backend/tests -name "test_*knowledge_builder*" -o -name "test_*landing*content*" \
  -o -name "test_*completion*" 2>/dev/null
```

## Output

- [ ] Inventario sales-agent fields + lógica.
- [ ] Inventario landing fields + transformations.
- [ ] Inventario completion logic + required mapping.
- [ ] Golden baseline capturado.
- [ ] Lista tests a preservar.
