# Pre-investigación obligatoria — Fase 08

## Sección 1 — Call sites de `get_catalog`

**Q1.1** — ¿Quién consume `get_catalog(domain)` y qué shape espera?

```bash
grep -rn "get_catalog\|FieldSpec" backend/src/modules/copilot --include="*.py"
```

Documentar shape esperado. Si callers leen `FieldSpec.path` + `.label`
+ `.section` + `.description` → projection mantiene.

## Sección 2 — Call sites de `schema_introspection`

**Q2.1** — ¿Qué helpers consumen `get_model_sections`, `validate_field_path`,
`unwrap_optional`?

```bash
grep -rn "schema_introspection\|get_model_sections\|validate_field_path" \
  backend/src/modules/copilot --include="*.py"
```

## Sección 3 — `propose_field_updates` flow

**Q3.1** — ¿Cómo valida paths el flow de write del copilot?

Documentar flow completo. Verificar que post-Fase 08 valida idéntico.

## Sección 4 — Acceptance tests existentes

**Q4.1** — ¿Hay tests acceptance/integration copilot que prueban
flows completos?

```bash
find backend/tests -path "*copilot*" -name "test_*"
```

## Sección 5 — `copilot/domain/offer_fields.py` post-Fase 04

**Q5.1** — ¿Sigue necesitándose como archivo separado o se promueve
consumers a leer `FieldContract` directo?

## Output

- [ ] Inventario call sites get_catalog.
- [ ] Inventario call sites schema_introspection.
- [ ] Flow propose_field_updates documentado.
- [ ] Tests acceptance identificados.
- [ ] Decisión sobre offer_fields.py.
