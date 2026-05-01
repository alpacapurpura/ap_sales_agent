# Prompt — Context prep PR-1-cascade-bugs-recovery (Haiku pre-flight)

> MANDATORY antes de spawn architect. Genera `CONTEXT-BRIEF.md` que el architect Opus consume INSTEAD of re-leer 30-50k de docs.

## Spawn pattern

```
Agent({
  description: "Pre-flight PR-1 cascade-bugs-recovery",
  subagent_type: "nicolify-context-builder",
  model: "haiku",
  prompt: <bloque abajo>
})
```

## Prompt body

```
Genera CONTEXT-BRIEF.md para este PR.

<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery
<modules>: brand, sales_agent
<phase>: architect
<subsystem_keywords>: personality_profile, model_dump, brand_data_adapter, knowledge_builder, litellm, llm_proxy, docker_mount, config_yaml

Sigue tu workflow estándar:
1. Read <pr_folder> files (PR.md). CONTRACT.md/IMPL-LOG.md/REVIEW*.md no existen aún.
2. Read current-state/brand.md + current-state/sales-agent.md
3. Load relevant rules: backend-ddd.md, anti-duplication.md, debugging.md, tdd-mandatory.md, parallel-safety.md
4. Run git diff main..HEAD --stat + --name-only
5. **Duplicate detection scan** (MANDATORY) — ejecutá los 6 grep commands per <subsystem_keywords> contra backend/src/core/, backend/src/shared/, backend/src/modules/{brand,sales_agent,copilot}/. Especial atención a:
   - Callers cross-codebase de `personality_profile.model_dump` o `PersonalityProfileModel.model_dump`
   - Callers de `brand_data_adapter.get_brand_knowledge`
   - Repository pattern para PersonalityProfile (ORM vs DTO Pydantic) en `backend/src/modules/brand/infrastructure/`
   - Otros sites que llamen `.model_dump()` sobre SQLA ORM models (mismo bug pattern potencial)
   - Docker compose mounts de litellm config
   - Existing helper para serializar SQLA → dict (`_to_json_dict`, `to_dict`, `model_to_dict`, etc.)
6. Cross-session overlap check: PI-4 S1 toca brand module (cleanup-buyer-persona). Verificá si paths PI-4 vs PI-7 PR-1 colisionan. Lista archivos en común (si hay) para architect Step 0.4.
7. Write CONTEXT-BRIEF.md con §1-§13 schema fully populated
   - § 7 Existing systems detected — verbatim grep results, table format
   - § 8 EXTEND-vs-NEW recommendations — mechanical rule (≥80% overlap → EXTEND, 40-79% → EXTEND with caveat, none → NEW)
   - § 11 Faithfulness gaps — flag any scan-incomplete or truncated reads
   - § 13 Verbatim grep commands executed (reproducibility)

Output path: <pr_folder>/CONTEXT-BRIEF.md

Last line of reply MUST be:
<!-- @pm: CONTEXT-BRIEF.md ready (faithfulness: clean|partial). Architect Opus puede consumir ahora. -->
```

## Cómo usar

PM lo invoca antes de architect spawn. Architect spawn lee CONTEXT-BRIEF.md como su entrada principal.
