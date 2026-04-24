# Pre-investigación obligatoria — Fase 06

## Sección 1 — Brand Pydantic surface

**Q1.1** — Lista exhaustiva `BrandSettings.model_fields` y nested models.

```bash
backend/.venv/bin/python -c "
from src.modules.brand.domain.brand import BrandSettings  # path real
for fname, finfo in BrandSettings.model_fields.items():
    print(f'{fname}: {finfo.annotation}')
"
```

(Verificar path real de la entity master. Brand domain tiene varios
archivos: identity.py, story.py, narrative.py, positioning.py, personality.py,
strategy.py, team.py, communication_assets.py.)

**Q1.2** — ¿La master entity es una sola Pydantic class o composición de
sub-models?

Si composición → walker recursivo igual que `Offer.specific_details`.

## Sección 2 — Section catalog brand

**Q2.1** — ¿Qué sections FE válidas tiene brand?

Source: `brand/domain/section_catalog.py` (creado en Fase 03 del refactor
anterior).

## Sección 3 — Drift audit

**Q3.1** — Diff entre `BRAND_EDITABLE_FIELDS` (~70 entries) y
`BrandSettings.model_fields user-facing`.

Esperado: drift confirmable. Cerrar el drift es ganancia de Fase 06
(igual que Fase 04 en offer).

## Sección 4 — Buyer-persona handling

**Q4.1** — ¿Buyer-persona vive como aggregate dentro de brand o
módulo separado?

Hoy es aggregate (`brand/domain/buyer_persona.py`). Decidir:
- Migra como módulo virtual `"buyer_persona"` dentro del brand registry?
- O Fase 07 lo separa antes de migrar?

Decisión bloqueante para Fase 06+07.

## Sección 5 — `project_brand_studio_refactor` status

**Q5.1** — ¿En qué sprint está el brand-studio refactor?

Memoria `project_brand_studio_refactor.md`. Coordinar para no-conflicto.

## Output

- [ ] Lista completa Pydantic brand fields.
- [ ] Section catalog brand confirmado.
- [ ] Drift audit completo.
- [ ] Decisión buyer-persona scope.
- [ ] Coordinación con brand-studio refactor.
