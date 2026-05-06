# Prompt — Context prep (Haiku pre-flight)

> **MANDATORY for PR ≥ M (medium).** PR-2 = L scope agentic-only → mandatory.
>
> Spawn `nicolify-context-builder` (Haiku 4.5) BEFORE architect / builder / auditor. Produces `CONTEXT-BRIEF.md` 3-5k tokens that downstream Opus/Sonnet agents consume INSTEAD of re-reading 30-50k of docs.
>
> **Critical reinforcement (origin: PR-3 PI-2 audit failure 2026-04-30):** § 7 + § 8 of CONTEXT-BRIEF do the cross-module duplicate scan that prevents architect from inventing parallel layers. The Haiku does this work; the Opus architect inherits the result.

## Spawn pattern (Agent tool)

```
Agent({
  description: "Pre-flight PR-2 telegram-orchestrator-hookup",
  subagent_type: "nicolify-context-builder",
  model: "haiku",
  prompt: <bloque abajo con valores reales>
})
```

## Prompt body

```
Genera CONTEXT-BRIEF.md para este PR.

<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup
<modules>: copilot, shared
<phase>: architect
<subsystem_keywords>: context_window, rolling_summarizer, system_prompt_layout, cacheable_fragments, cache_boundary, tool_registry, available_channels, format_for_channel, escape_markdown_v2, copilot_orchestrator, telegram_worker, conversation_repository, channel_chat_id

Sigue tu workflow estándar:
1. Read <pr_folder> files (PR.md obligatorio; CONTRACT.md/UI-SPEC.md/IMPL-LOG.md/REVIEW*.md si existen — en pre-flight architect aún no existen)
2. Read current-state/copilot.md (capability live PR-1 + lineage)
3. Read PR-1 RESULT.md + handoff.md S1 (surface live disponible para reusar)
4. Load relevant rules: copilot-resilience, copilot-observability, backend-ddd, architectural-fitness, master-data, currency-handling (skim per <modules>)
5. Run git diff main..HEAD --stat + --name-only (capturar cambios PR-1 ya commiteados)
6. **Duplicate detection scan** (MANDATORY architect phase) — ejecutá 6 grep commands per <subsystem_keywords>:
   - grep -rn "ContextWindowConfig\|ContextWindowBuilder\|RollingSummarizer\|RAW_WINDOW_TOKENS" backend/src/modules/copilot/
   - grep -rn "CACHEABLE_FRAGMENTS\|CACHE_BOUNDARY_MARKER\|system_prompt_layout\|STATIC_IDENTITY" backend/src/modules/copilot/
   - grep -rn "ToolGroupMeta\|available_channels\|get_tools_for_context\|is_group_available_in_channel" backend/src/modules/copilot/
   - grep -rn "format_for_channel\|escape_markdown_v2\|parse_mode" backend/src/modules/copilot/ backend/src/shared/
   - grep -rn "invoke_copilot_orchestrator\|run_orchestrator\|CopilotOrchestrator" backend/src/modules/copilot/application/orchestrator/
   - grep -rn "CopilotConversationRepository\|get_by_channel\|channel_chat_id\|get_or_create" backend/src/modules/copilot/
7. Write CONTEXT-BRIEF.md con §1-§13 schema fully populated:
   - § 7 Existing systems detected — verbatim grep results, table format con paths exactos + LOC referenciadas
   - § 8 EXTEND-vs-NEW recommendations — mechanical rule (≥80% overlap → EXTEND, 40-79% → EXTEND with caveat, none → NEW). Para PR-2 esperamos TODO EXTEND (PR-1 ya creó tablas + ToolGroupMeta + adapter; S2 cablea sin nuevas capas)
   - § 11 Faithfulness gaps — flag scan-incomplete o truncated reads
   - § 13 Verbatim grep commands executed (reproducibilidad)

Output path: <pr_folder>/CONTEXT-BRIEF.md

Last line of reply MUST be:
<!-- @pm: CONTEXT-BRIEF.md ready (faithfulness: clean|partial). Downstream agent (architect) can consume it now. -->
```

## Cómo usar

1. Chris ejecuta este prompt con Agent tool (`subagent_type: nicolify-context-builder`, `model: haiku`).
2. Haiku lee PR.md + S1 surface + corre 6 greps + escribe CONTEXT-BRIEF.md.
3. Architect Opus en siguiente fase lee SOLO CONTEXT-BRIEF.md (no re-lee 30-50k de docs).

## Cuándo NO ejecutar

- Re-audit con CONTEXT-BRIEF.md ya generado y vigente (mismo commit hash) — context-builder es idempotente, output sería igual.
- PR S (bug-fix simple) — no aplica a PR-2 (es L).

## Anti-patterns

- ❌ Spawn context-builder sin `<subsystem_keywords>` (pierde valor de § 7 + § 8 — duplicate scan se hace genérico)
- ❌ Architect ignora § 7 + § 8 al diseñar (duplicado downstream → audit FAIL "NO-NEW-LAYER violation")
- ❌ Spawn con `model: "sonnet"` (es Haiku — overcost 5×)
- ❌ Re-leer todo el repo después del brief porque "no confío en Haiku" (la pre-validación es § 11 Faithfulness — si flag clean, confía)

## Auto-loop integration

```
00-context-prep    (Haiku)   ← este prompt
   ↓
01-architect-start (Opus)    ← lee CONTEXT-BRIEF.md, produce CONTRACT.md
   ↓
02-builder-start   (Opus — agentic surface)  ← lee CONTEXT-BRIEF + CONTRACT + spawnea gate-runner Haiku + auditor Opus
   ↓
03-auditor-start   (Opus)    ← lee CONTEXT-BRIEF + gate-output.json + diff
   ↓
04-pm-close        (PM)      ← lee REVIEW-agentic.md + actualiza current-state/copilot.md
```

Para fix-loop iteraciones (iter 2-3): NO re-spawn context-builder. El brief original se mantiene válido.
