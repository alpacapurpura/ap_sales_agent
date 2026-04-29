# Handoff prompt · S12 start

> **Refinado al cierre de S11. Cierre formal del plan — cero deuda flotante.**

---

```
Cierre del redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S12 — Final hardening + zero debt
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
📝 Aprendizajes previos: learnings/S0..S11.

CONTEXTO:
- S0..S11 cerrados. S11 = S11A (`8cc9ea2c`) + S11B (commit final
  `7367b5f8`).
- Eval loop S10 activo (semanal cron + goldens).
- Orchestrator decomposed (chat.py 337 LOC bajo ceiling 400 arch ratchet
  `test_chat_orchestrator_loc_ratchet.py`); 4 collaborators extraídos
  (`AuditEmitter`, `IdentityResolver`, `ConversationPipeline`,
  `smart_debounce_runner`); closer_studio split en
  Query/Command/Kpi + facade back-compat; semantic_router con domain
  SYSTEM_ROUTES + application overlay + thin singleton.
- Callback handler shared base lift completo (Sales + Copilot < 200 LOC cada uno).
- Snapshot byte-equal framework activo en
  `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py`
  (1 escenario telegram new lead) + S11A
  `tests/shared/agent_observability/test_callback_handler_snapshot.py`.
  S12 NO debe extender estos snapshots salvo regresión específica.

TECH DEBT EN RADAR S12 (4 nuevas DEFERRED-S12 desde S11B):
- `_tool_dedup_tracker` magic string (S1) — TypedDict update.
- Lazy imports brand+offer (S00) — probable WONT-FIX (ratchet ok).
- Subscribers SessionLocal-per-event (S1) — probable WONT-FIX.
- `knowledge_builder.py` factory amplio (S00) — probable WONT-FIX.
Todas reabren a S12 según `05-tech-debt-log.md` "Detectados durante S11B".

ENTREGABLES S12 (cierre del plan):

1. Tier pricing >200k arch ratchet:
   - tests/architecture/test_pricing_tier_resolution_completeness.py
   - Si LiteLLM JSON declara input_cost_per_token_above_200k_tokens
     para algún provider y el calculator no resuelve tier → CI falla.
   - Implementar tier resolution en
     src/shared/agent_observability/cost/calculator.py.
   - Cierra watchpoint S2.

2. typing_simulation_cpm wiring:
   - OutputManager._calculate_typing_time consume
     fmt.typing_simulation_cpm or cls.CPM_SPEED.
   - §3 fragment validado por goldens eval loop S10 → diff = 0
     post-wiring (si > 0, validar empíricamente que mejora UX).
   - Cierra deuda S5 FLAGGED.

3. DeepSeek alias retire validator + Kimi conv monitor:
   - Si no se hicieron en S10, cerrar acá.
   - test_deepseek_alias_not_retired (judge multi-rubric).
   - Streamlit /sales-routing dashboard conv rate per (tenant,
     model_responded). Alert si < baseline -5%.

4. Presidio classification:
   - Mover entry [MEDIUM] PII async post-write worker (Presidio + spaCy NER)
     a WONT-FIX en 05-tech-debt-log.md.
   - Razón documentada: "Regex sync cubre 80% PII LATAM. Presidio
     overhead 50-200ms incompatible con hot-path <10ms p99 target.
     Reabrir si emerge tenant enterprise con requirement explícito en
     contrato firmado."

5. Scan voseo final:
   - regex de .claude/rules/spanish-text.md sobre sales_agent/ +
     shared/agent_observability/ + brand_voice integration paths.
   - Hits inesperados (no tenant override) → fix.

6. Audit final 05-tech-debt-log.md:
   - bash check: grep -E "^- Acción: DEFERRED-" → cero líneas.
   - Cada FIXED tiene commit hash.
   - Cada WONT-FIX tiene razón explícita + condición de reapertura.
   - FLAGGED entries archivadas a "Resolved watchpoints" section.

7. Skill /salesagent-expert (PERMANENTE — guía senior+arquitecto+CTO):
   - Crear `.claude/skills/salesagent-expert/SKILL.md` (frontmatter +
     8 secciones — ver phases/S12-* "Entregable: skill /salesagent-expert").
   - SOLO carga decisiones permanentes: §3 protected, principios senior,
     anti-patterns cerrados, decisiones cross-fase no obvias, glossary,
     pointers permanentes a docs estables, checklist pre-commit.
   - NO carga: paths específicos, LOC counts, lista tests, allowlists
     ratchets, schemas Pydantic, listado tools, modelos LLM concretos.
   - Verificar si .claude/skills/sales-agent-expert/ existe (guión
     intermedio) — decidir merge vs replace según contenido + user.
   - Test manual del skill con fix ficticio que rompería §3 — debe
     responder escalation, no code.
   - ≤ 8000 chars SKILL.md.

PROTOCOLO:

1. Lee: README + 00 (§4 Definition of Done por fase + DoD plan completo
   en 01) + 01 + 02 + 03 + 04 + 05 (ENTERO) + learnings/S0..S11 +
   phases/S12-* + .claude/rules/architectural-fitness.md.

2. Research mandate:
   - "LiteLLM model_prices_and_context_window tier pricing 2026"
   - "Postgres conversion rate aggregate query optimization 2026"
   - "Python regex PII LATAM compliance LGPD LFPDPPP PDPA scope 2026"

3. Audit ENTRY-BY-ENTRY de 05-tech-debt-log.md:
   - Para cada DEFERRED-*: ¿la fase target ya cerró? ¿la entry tiene
     FIXED hash? Si NO → identificar gap y resolver acá.
   - Si externa/operacional → WONT-FIX con razón + reapertura
     condicional.

4. TaskCreate granular.

5. TDD:
   - RED: arch test tier pricing (sin tier resolution implementado).
   - Implementar tier resolution. GREEN.
   - RED: test typing_cpm wiring contra OutputManager.
   - Wire. Goldens diff = 0.
   - Re-classify Presidio.
   - Cerrar S10 watchpoints (DeepSeek + Kimi) si no fueron.
   - Voseo scan + fix.
   - Audit final.

6. Quality gates:
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/pytest tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/modules/sales_agent/
     tests/modules/copilot/ tests/admin/ tests/shared/ tests/modules/brand/ -x -q
   - Goldens eval loop diff = 0.
   - Voseo scan grep retorna 0 hits inesperados.
   - bash check tech-debt-log: cero DEFERRED entries.

7. Verificación funcional final:
   - Conversación dev sales_agent en cada canal (chat / whatsapp /
     telegram / instagram_dm / sms / voice / email) — output normal.
   - §3 protected smoke OK.
   - Eval loop S10 corre weekly cron sin errores.
   - Streamlit /costo-agentes + /sales-routing renderean con data live.

8. Tech debt closure final — TODOS los entries DEFERRED del log a
   FIXED o WONT-FIX:
   - [MEDIUM] LiteLLM tier pricing > 200k tokens (S2) → FIXED.
   - [LOW] typing_simulation_cpm declarado pero no consumido (S5) → FIXED.
   - [MEDIUM] PII async post-write worker Presidio (S2) → WONT-FIX.
   - [MEDIUM] DeepSeek alias retire 2026-07-24 (S4) → FIXED via S10/S12.
   - [LOW] Closer temp 0.4 clamped a 0.6 (S4) → FIXED via S10/S12 monitor.
   - Cualquier otro entry DEFERRED-* que emerja del audit → resolver.

9. learnings/S12-*.md (denso, accionable, audit del plan completo).

10. README estado fase ✅ S12. Plan cerrado.

11. Commit final: `feat(sales-agent-redesign-s12): final hardening — plan close-out, zero floating debt`

CRITERIO DE ÉXITO ABSOLUTO (DoD plan completo):
- 05-tech-debt-log.md: cero entries DEFERRED-* flotantes.
- Cada arch invariante del plan tiene fitness test.
- Reconciliation worker dual-write parado.
- Eval loop S10 activo y verde.
- chat.py < 400 LOC, closer_studio_service.py split,
  semantic_router.py registry.
- Backlog general producto recibe items operacionales NO del plan
  (alias retires futuros, requirements enterprise) con WONT-FIX o
  reapertura condicional.
- §3 protected verificado intacto smoke final.
- README todas las fases ✅ DONE.

Si UNO falla → S12 NO cerrada. Plan NO declara success hasta los 8
DoD criteria del 01-master-plan.md.

Empieza con paso 1.
```
