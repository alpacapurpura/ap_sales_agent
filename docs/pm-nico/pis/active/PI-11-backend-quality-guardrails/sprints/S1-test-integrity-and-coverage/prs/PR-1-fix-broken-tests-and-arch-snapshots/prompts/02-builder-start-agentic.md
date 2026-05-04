# Prompt — Builder kickoff (Agentic surface)

> Builder: `nicolify-agentic` (Opus)
> Surface: `sales_agent`, `copilot`

## Spawn pattern

```
Agent({
  description: "Build PR-1 agentic surface",
  subagent_type: "nicolify-agentic",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos nicolify-agentic (Opus). Trabajo: fixear tests rotos de surface agentic en PR-1.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Restricciones DURAS:
- Tocás SOLO archivos de sales_agent y copilot (tests/ y src/ si bug real).
- NO tocás modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm}/.
- NO tocás archivos de otros PRs activos.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify.
- Push falla non-fast-forward → STOP, reportar.

Skills obligatorios (invocar ANTES de tocar código):
- copilot-expert
- sales-agent-expert
- tessl__langgraph

Workflow Phase 1 — IMPLEMENT:
1. Fix tests agentic surface (lista abajo).
2. Quality gates locales NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/pytest tests/modules/sales_agent/prompts/ tests/modules/copilot/ tests/architecture/test_sales_agent_system_prompt_order.py tests/architecture/test_sales_agent_anchors.py -v --timeout=60
3. Stage + conventional commit + push origin development.
4. IMPL-LOG.md completo.

Workflow Phase 2 — AUTO-AUDIT:
5. Spawn nicolify-gate-runner Haiku:
   Agent({ description: "Run gates iter-1", subagent_type: "nicolify-gate-runner", model: "haiku",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <command>: test-backend; <iter>: 1" })
6. Esperá gate-output.json. Si any_fail en gates 3-7,11-13 → fix, re-commit, re-spawn.
7. Spawn nicolify-agentic-auditor Opus:
   Agent({ description: "Audit PR-1 agentic", subagent_type: "nicolify-agentic-auditor", model: "opus",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <surface>: agentic; <iter>: 1" })
8. Si verdict ≠ PASS → fix loop max 3 iter.

Outputs:
- Code + tests committed + pushed
- IMPL-LOG.md
- gate-output.json final
- REVIEW-agentic.md (output auditor)

[BLOQUE VARIABLE]

Tests a fixear (agentic surface):
1. tests/modules/sales_agent/prompts/test_compose_system_prompt.py::TestFragmentOrderInvariants::test_cacheable_fragments_match_s3_plan
   - Left contains CAMPAIGN_CONTEXT. Agregar a tupla esperada.
2. tests/architecture/test_sales_agent_system_prompt_order.py::test_cacheable_fragment_order_is_frozen
   - Igual: agregar CAMPAIGN_CONTEXT a EXPECTED_CACHEABLE.
3. tests/architecture/test_sales_agent_system_prompt_order.py::test_full_order_is_cacheable_then_volatile
   - Orden total cambió. Actualizar EXPECTED_CACHEABLE + EXPECTED_VOLATILE.
4. tests/architecture/test_sales_agent_anchors.py::test_all_sales_agent_anchors_are_registered
   - Nuevo anchor SALES-AGENT-OUTBOUND-PR7 sin entry en ANCHOR_REGISTRY. Agregar.
5. tests/modules/copilot/test_voice_api.py::test_transcribe_audio_logs_tenant_context
   - Endpoint legacy retorna 410 Gone. Decisión: adaptar test a 410 o eliminar test legacy.
6. tests/modules/copilot/test_voice_api.py::test_transcribe_audio_success
   - Idem: 410 Gone.
7. tests/modules/copilot/test_voice_combined.py::test_legacy_transcribe_endpoint_still_works
   - Idem: 410 Gone.
8. tests/modules/copilot/test_offer_section_tools.py::TestAdaptFromBrandIdentity::test_missing_brand
   - result["suggestions"] == [] pero test espera len > 0. Verificar si es bug o test desactualizado.
9. tests/modules/copilot/test_deep_agent_factory_wire.py::TestFactoryTemperatureOverride::test_kimi_k2_temperature_clamped_for_agent_role
   - temperature=1.0 no se clampea a 0.6. Verificar si es bug real en LLMFactory.
10. tests/modules/copilot/test_outbox_adapter_integration.py::TestCopilotOutboxAdapterFlagOff::test_flag_off_is_default_for_copilot_module
    - Assert False; retorna True. Mismo que brand.
11. tests/modules/copilot/test_outbox_adapter_integration.py::TestCopilotOutboxAdapterFlagOff::test_monkeypatch_env_flag_off
    - monkeypatch no surte efecto. Investigar _is_outbox_enabled.
12. tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot
    - (Verificar si sigue roto; en última ejecución pasó, pero podría ser flaky.)
13. tests/integration/test_outbound_orchestrator_e2e.py::test_outbound_orchestrator_success_with_real_db_tenant_and_lead
    - AttributeError: build_sales_agent_callback_handler no existe en módulo. Actualizar patch path.

Código posible a tochar:
- src/modules/sales_agent/application/orchestrator/chat.py (si prompt fragment drift)
- src/shared/infrastructure/llm/factory.py (temperature clamping)
- src/modules/copilot/application/tools/offer_section_tools.py (suggestions empty)
- src/modules/copilot/api/voice.py (410 endpoint legacy — solo si se decide cambiar comportamiento)

PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
Surface: agentic
Iter actual: 1
```
