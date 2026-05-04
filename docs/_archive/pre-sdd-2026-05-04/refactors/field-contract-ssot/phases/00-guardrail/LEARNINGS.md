# Fase 00 — Learnings

Completada al cierre de la fase. Feeds `../../LEARNINGS.md` cross-cutting.

## Descubrimientos técnicos

- **Allowlist real = 59, no 9.** Audit de `OFFER_SCHEMA_REGISTRY` con filtro
  edition-level destapó la brecha completa (pricing + authority + value-stack +
  program narratives + subscription/service/product renames/fills + PLATFORM
  archetype + cross-module federado). Ver ADR-007.
- **`SubscriptionDetails` rename drift** entre FE (`billing_frequency`,
  `content_update_frequency`) y BE (`billing_cycle`, `content_update_freq`).
- **PLATFORM archetype huérfano:** `platform-details.schema.ts` declara 14
  paths sin contraparte en `ARCHETYPE_TO_DETAILS_MAPPING`.
- **Cross-module federado (21 paths):** assets, buyer-persona, social-proof,
  scheduling, knowledge, gallery, faq.
- **WSL2 no rutea al bridge Docker.** Scripts que piden DB local (capture
  baseline) corren dentro de `visionarias_brain_dev` y el JSON sale con
  `docker cp`.
- **`model_registry` import obligatorio** en scripts standalone; sin él,
  SA no resuelve relaciones string y rompe al primer query.
- **`LandingService.generate_landing_for_offer` persiste.** Para snapshot
  dry-run replicamos la query SQL + `_resolve_content()` puro en el script.
- **Item-level (itemSchema.fields[].path) validation** fuera de scope Fase
  00. Solo se excluyen del check top-level para evitar falsos positivos.

## Deuda técnica encontrada

Registrada en `../../LEARNINGS.md` + `docs/mejoras-proceso/to-do.md`:

- Rename `billing_cycle → billing_frequency`,
  `content_update_freq → content_update_frequency` en `SubscriptionDetails`
  + migration idempotente. Fase 02.
- Modelar `PlatformDetails` + registrar en `ARCHETYPE_TO_DETAILS_MAPPING`.
  Fase 02.
- Extender resolver del arch test a paths federados (assets/social-proof/
  scheduling/knowledge). Fase 05.
- Validación item-level (`pricing_options[].label` resuelve contra
  `PricingStructure`). Fase 01+.

## Sorpresas

- La fase arrancó asumiendo 9 paths huérfanos por capa A; terminó con 59.
- El script de captura tomó 4 iteraciones (env `.env` override → brain
  container → `model_registry` → permisos FS) antes de producir el fixture.
- Script captura reutiliza `_resolve_content()` puro — no hay que duplicar
  content-building logic del landing service.

## Ajustes al patrón para fases siguientes

- **Medir antes de fijar caps.** Antes de escribir ADR con valor numérico
  para ratchets, correr el test contra el repo y contar.
- **Scripts BE con DB local van dentro del container.** Incluir instrucción
  de `docker cp` en docstring + `--output` CLI flag.
- **Importar `model_registry` en todo script standalone.** Añadir regla a
  `.claude/rules/backend-ddd.md` si aparece tercer caso.
- **Documentar cross-module ownership** en el SPEC de cada fase para que
  la categorización de la allowlist tenga base antes de empezar a escribir.

## Decisiones nuevas (ADR-NNN candidates)

- ADR-007 — Allowlist cap de Fase 00 arranca en 59, no en 9.
