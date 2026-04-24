# Field Contract Platform — refactor cross-module

## Por qué existe este workspace

Sucesor de `docs/refactors/field-contract-ssot/`. El refactor original
arrancó con scope offer-aislado. Al abrir Fase 04 descubrimos que el
problema **no era de offer** sino del platform: 5 fuentes paralelas
sobre fields/sections viviendo en offer + brand + buyer-persona +
copilot, todas parcialmente solapadas, todas manuales, todas con drift.

Continuar el refactor original consolidaba el frankenstein. Lo correcto
es **diseñar el contrato cross-module una vez** y aplicarlo
incrementalmente a cada módulo, manteniendo experiencia de usuario
intacta.

Decisión documentada en [DECISIONS.md](DECISIONS.md) ADR-011.

## Objetivo final

> Un único `FieldContract` en `shared/domain/` que sirve como SSoT
> estructural + semántico + lifecycle + copilot-meta para cualquier
> módulo. Pydantic provee la estructura, FieldContract enriquece, FE
> schemas presentan, todos los consumers (form-runtime, copilot
> conversacional, sales-agent, landing, extraction, completion)
> proyectan del contract sin drift.

## Drivers de producto

- **Copilot conversacional reemplaza la web** vía whatsapp/telegram.
  Cada field necesita `human_question_es`, `expects`, `gate`,
  `redo_if_changes` para que el LLM pueda preguntar naturalmente.
- **Lifecycle de fields** (agregar/agrupar/eliminar/deprecar) sin
  romper consumers viejos: `status`, `deprecated_in`, `replaced_by`.
- **Multi-module consistency**: 17 módulos hoy, más por venir. Sin un
  patrón único, drift compuesto es inevitable.
- **Claude trabaja con vista local**: el sistema debe ser
  autodocumentable — abrir un archivo y entender el módulo.

## Estructura de fases

| Fase | Objetivo | Estado |
|---|---|---|
| 04 | Platform foundation + offer pilot end-to-end | in-progress |
| 05 | Sales-agent + landing + completion data-driven | pending |
| 06 | Brand migration | pending |
| 07 | Buyer-persona migration | pending |
| 08 | Copilot unification (read + write surfaces) | pending |
| 09 | Multi-channel projection (web + conversational) | pending |

## Reglas inquebrantables

Ver [INVARIANTS.md](INVARIANTS.md). Resumen:

- Additive antes de subtractive.
- Un concepto por commit.
- UX byte-identical en cada commit.
- Arch tests verde cada commit.
- Pre-investigación obligatoria antes de cada fase
  (ver `phases/{NN}/PRE_INVESTIGATION.md`).
- SSoT no negociable: ningún registry paralelo nuevo.
- Brand/buyer/copilot no se rompen mientras se migran.

## Cómo retomar

Cualquier sesión Claude que retoma este refactor:

1. Lee [STATE.md](STATE.md) (estado actual).
2. Lee [protocol/RESUME.md](protocol/RESUME.md).
3. Lee la fase activa: `phases/{NN-name}/PRE_INVESTIGATION.md` →
   `SPEC.md` → `STATUS.md`.
4. Ejecuta `protocol/PRE_FLIGHT.md`.
5. Sigue commits atómicos. Cada commit reverible.

## Workspace anterior

`docs/refactors/field-contract-ssot/` queda como histórico (Fases 00-03
cerradas allá). Fase 04 originalmente planeada se reformuló acá.
Redirect documentado en su `STATE.md`.
