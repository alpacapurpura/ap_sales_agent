# Golden fixture — Offer `a96403b5-c1db-4b31-97aa-cb18d08ad9f9`

Baseline para no-regresión durante refactor field-contract-ssot.

## Identificación

- `tenant_id`: `1fd1562b-2101-410a-870c-dc2f7e27b355`
- `offer_id`: `a96403b5-c1db-4b31-97aa-cb18d08ad9f9`
- `name`: Programa de Proposito a Prosperidad
- `archetype`: `programa`
- `preset_id`: `coach_bootcamp`
- `value_level`: `transformacion`

## Qué contiene el fixture

`backend/tests/modules/offer/fixtures/offer_a96403b5_baseline.json` con:

1. **DB state snapshot**: `Offer.model_dump(exclude={timestamps, ephemeral})`
2. **Sales-agent prompt rendered**: string final de `agent_identity.j2` con este offer
3. **Landing output**: `landing_service.generate_landing_for_offer(tenant, offer_id, dry_run=True)` → `LandingPageConfig.model_dump()`

## Test que verifica paridad

`backend/tests/modules/offer/test_offer_a96403b5_baseline.py`:

- Test 1: DB state del offer == baseline (additive allowed, subtractive forbidden)
- Test 2: Prompt rendered == baseline (additive only; nuevo bloque solo si offer tiene field nuevo seteado)
- Test 3: Landing output == baseline (additive only)

## Cuándo regenerar baseline

**Regenerar solo cuando cambio arquitectónico legítimo agrega valor al baseline.** Nunca por conveniencia.

Legítimo:
- Fase 01 cierra: offer ahora tiene `tax_included=null` (field nuevo agregado al domain). Baseline regenera agregando la key con null. Entry DECISIONS.md ADR-NNN explicando.
- Nueva fase agrega narrative field extraído: baseline agrega field.

NO legítimo:
- "El test falla, regenero para que pase" sin entender diff.
- Offer cambió en dev manualmente y quiero sincronizar.

## Cómo regenerar

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/python scripts/regenerate_offer_baseline.py \
    --tenant-id 1fd1562b-2101-410a-870c-dc2f7e27b355 \
    --offer-id a96403b5-c1db-4b31-97aa-cb18d08ad9f9 \
    --output tests/modules/offer/fixtures/offer_a96403b5_baseline.json
```

(Script a crearse en Fase 00 sub-step 1.)

Revisar diff ANTES de commitear. Cualquier subtractive = STOP.

## Fields sensibles a regenerar con cuidado

- `completion_percentage` — cambia si `_SECTION_VALIDATORS` cambia (Fase 05 lo tocará)
- `specific_details.current_enrollment_count` — puede cambiar por data entry real en dev
- Fields narrativos recién agregados — deben aparecer solo cuando offer tiene data real

## Referencia

- Fase 00 SPEC sub-step 1
- INVARIANTS.md §3, §6, §7, §8
