# Handoff prompt · S10 start

> **Refinado al cierre de S9.**

---

```
Continuamos redesign sales_agent — fase final.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S10 — Quality eval loop (judge + goldens)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md
📝 Aprendizajes: learnings/S7-*, S8-*, S9-*.

CONTEXTO:
- Todas las features anteriores cerradas. Sales_agent: voz de marca + scheduler + payment + access automático.
- Copilot tiene F9 quality eval implementado — espejar pattern.
- Branch: development limpio.
- Último commit: {S9_COMMIT_HASH} (ver git log)
- Hooks: callback handler con costo, brand_voice_summary, scheduler tools, payment tools.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S7-S9 + phases/S10.
2. Research mandate: LLM judge multi-rubric sales eval 2026, LangChain Evaluator vs LLM-judge, golden test set creation 2026, prompt cache invariance brand voice eval.
3. Lectura: copilot judge.py (F9), copilot golden tests, learnings F9 copilot redesign.
4. TaskCreate.
5. TDD:
   - test_sales_agent_judge_stub
   - test_golden_runner (~20 goldens, baseline ≥0.75)
   - test_brand_voice_differentiation_goldens
   - test_quality_judge_no_pii_in_prompt
   - test_quality_dashboard_smoke
6. Implementar SalesAgentJudge + 5-dim rubric.
7. Goldens initial set cubriendo:
   - rapport→discovery
   - manejo objeciones
   - cierre + payment link
   - booking link
   - multi-canal (whatsapp/telegram/ig/web/sms/email)
   - voz tenant A vs B
8. Cron weekly_sales_agent_quality_eval ARQ.
9. Streamlit /sales-agent-quality dashboard.
10. Drift threshold alert.
11. Quality gates.
12. §3 sigue funcionando.
13. Tech debt log: si goldens revelan bugs en S0-S9 → log DEFERRED.
14. learnings/S10-*.md.
15. Reportar al usuario plan completado.

PRINCIPIOS:
- Stub default + RUN_LLM_JUDGE=1 opt-in (cost guard).
- PII sanitization en judge prompt (no incluir raw input).
- Goldens fixtures sintéticas (no PII real).
- Snapshot test stub vs real cada N semanas.

Esta es la fase final del plan. Asegurar:
- README.md status table actualizada (todas DONE).
- Reporte final al usuario con resumen de los 11 sprints.

Empieza con paso 1.
```
