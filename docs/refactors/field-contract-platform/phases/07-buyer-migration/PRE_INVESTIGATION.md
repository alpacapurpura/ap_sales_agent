# Pre-investigación obligatoria — Fase 07

## Sección 1 — Buyer-persona Pydantic surface

**Q1.1** — Modelo completo `BuyerPersona`.

```bash
backend/.venv/bin/python -c "
from src.modules.brand.domain.buyer_persona import BuyerPersona  # path real
for fname, finfo in BuyerPersona.model_fields.items():
    print(f'{fname}: {finfo.annotation}')
"
```

**Q1.2** — Composables / nested models: `pain_points`, `desires`,
`day_in_life`, etc.

## Sección 2 — Section catalog

**Q2.1** — ¿Buyer-persona tiene su propio section_catalog o reusa brand?

## Sección 3 — Module registration name

**Q3.1** — `register_module_contracts("buyer_persona", ...)` o ¿se
unifica con brand?

Decisión consistente con Fase 06.

## Output

- [ ] Lista Pydantic completa.
- [ ] Section catalog confirmado.
- [ ] Module name decidido.
