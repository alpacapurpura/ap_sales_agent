# Handoff prompt · S6.5 start

> **Refinado al cierre de S6 (2026-04-28). Trigger: 2026-05-26 (4 semanas dual-write window).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S6.5 — Legacy drop + admin cutover
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S6-5-legacy-drop-admin-cutover.md
📝 Aprendizajes previos: learnings/S0..S6.

CONTEXTO post-S6 (cerrado 2026-04-28):
- S6 cerrada: 6 arch fitness tests congelan estado infra post-S0..S5.
  Sweeps S4/S5 ejecutados (shim cleanup copilot + LLM_ROLE_BY_SITE expansion).
- Branch: development limpio. Último commit S6: c02d4ba2.
- Reconciliation worker S1 corriendo cron @ minute=25, midiendo diff
  legacy vs event-sourced por tenant.
- sales_audit.py dual-read activo (banner UI + sidebar prefer event-sourced).

PRE-CONDICIÓN BLOQUEANTE para ejecutar S6.5:
1. Verificar fecha actual >= 2026-05-26 (4 sem desde S1 close).
2. Query reconciliation_runs table: diff < 1% durante últimas 2 sem
   consecutivas.
3. sales_agent_trace_event + sales_agent_llm_call poblados continuamente
   sin gaps de tiempo > 1 hora.

Si alguna condición FALLA → POSTPONER 2 semanas + investigar drift.
NO ejecutar drop bajo presión.

ENTREGABLES S6.5:
- Migración Alembic idempotente: DROP TABLE IF EXISTS agent_traces +
  llm_logs (CASCADE solo si FKs incoming detectadas).
- Cutover sales_audit.py: borrar import AgentTrace + branch dual-read
  legacy + queries LLMLogModel. Solo lectura event-sourced queda.
- AuditRepository.clear_user_history: solo MessageModel +
  sales_agent_trace_event + sales_agent_llm_call + AgentStateCheckpoint.
- Files borrados: agent_trace_model.py + llm_log_model.py +
  infrastructure/monitoring/tracing.py (decorator @trace_node).
- Worker dual_write_reconciliation_task desregistrado de WorkerSettings
  + SchedulerSettings.cron_jobs.
- Arch tests nuevos (sin allowlist):
  - test_no_legacy_agent_trace_reads.py
  - test_admin_no_legacy_table_reads.py
  - test_no_future_annotations_in_langgraph_files.py (cierra watchpoint S1)
- Cleanup docs: corregir agent_log_model → LLMLogModel references en
  02-architecture-target.md + audit/sales-agent-current-state.md +
  tech-debt-log entries históricos.

PROTOCOLO:

1. Lee: README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S0..S6 +
   phases/S6-5 + audit/admin-migration-plan.md §2 Fase C +
   .claude/rules/backend-migrations.md.

2. Research mandate:
   - "Alembic drop table production safe rollback strategy 2026"
   - "Postgres DROP TABLE active connections lock contention 2026"

3. Pre-flight check obligatorio:
   - SQL query reconciliation_runs últimas 2 sem.
   - Si drift > 1% → ESCALAR al usuario, NO proceder.

4. TaskCreate granular.

5. TDD:
   - Arch tests RED primero (test_no_legacy_agent_trace_reads,
     test_admin_no_legacy_table_reads, test_no_future_annotations).
   - Cutover sales_audit.py → tests GREEN.
   - Borrar files Python legacy → tests siguen GREEN.
   - Migration drop tablas → idempotente verify clone.

6. Quality gates:
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/pytest tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/admin/ -x -q (smoke verde
     post-cutover)
   - cd backend && .venv/bin/pytest tests/modules/sales_agent/ -x -q
   - Migration apply en clone DB + idempotent re-run = 0 cambios.

7. Verificación funcional:
   - Streamlit admin /auditoria render sin exception, sin banner
     dual-read, sólo lectura event-sourced.
   - Closer Studio + ws + webhooks intactos (§3).
   - Reconciliation worker NO corre más (verificar logs).

8. Tech debt log: marcar FIXED con commit hash:
   - [HIGH] Sales_agent sin retention policy (S1)
   - [HIGH] Streamlit sales_audit.py lee tabla legacy (S0)
   - [LOW] agent_log_model mencionado en docs no existe (S1)
   - [LOW] from __future__ import annotations rompe LangGraph (S1)
   - [HIGH] Drop tablas legacy agent_trace_model + LLMLogModel (S6)

9. learnings/S6-5-*.md + prompts/S7-start.md refinado (si aplica).

10. README estado fase ✅ S6.5.

11. Commit: `feat(sales-agent-redesign-s6-5): drop legacy tables + admin cutover post dual-write window`

PRINCIPIOS:
- Pre-flight check NO negociable: drift > 1% → ABORT.
- Drop irreversible: probar idempotency en clone DB obligatorio.
- §3 protected intacto.
- Stage por nombre en commits.
- Spanish neutro LATAM.

Empieza con paso 1.
```
