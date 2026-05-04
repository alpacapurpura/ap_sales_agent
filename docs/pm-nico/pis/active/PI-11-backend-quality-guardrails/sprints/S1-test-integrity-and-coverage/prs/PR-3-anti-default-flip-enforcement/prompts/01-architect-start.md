# Prompt — Architect kickoff (PR-3)

> **Architect Opus PR-3 está incluido en la ejecución compartida con PR-1.**
> Ver `PR-1/prompts/01-architect-start.md` — produce CONTRACT.md PR-1 + CONTRACT.md PR-3 cross-linked en una sola spawn.
>
> **NO spawnees architect separado para PR-3.** Si por alguna razón se necesita re-spawn solo PR-3 (ej. PR-1 ya shipped y PR-3 cambia), usar este prompt como fallback.

## Spawn pattern (fallback solo)

```
Agent({
  description: "Architect PR-3 standalone (fallback)",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
Sos `nicolify-architect` (Opus). Trabajo: producir CONTRACT.md PR-3 (anti-default-flip enforcement).

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Lectura obligatoria:
1. {pr_folder}/CONTEXT-BRIEF.md
2. {pr_folder}/PR.md
3. PI-11/PI.md § Decisión arquitectónica clave (D1-D7)
4. .claude/rules/anti-duplication.md (estructura inspiración)
5. backend/tests/architecture/ (patrón ratchet existing)
6. backend/src/shared/domain_events/legacy_event_bus.py
7. backend/src/shared/domain_events/outbox/application/event_bus_adapter.py
8. CLAUDE.md (conditional rules section)

CONTRACT.md PR-3 sections:
- § 0 Context Summary (date, dependencies on PR-1)
- § 1 Rule design `.claude/rules/anti-default-flip-audit.md` (estructura completa, ejemplos, anti-patterns, enforcement layers)
- § 2 Arch fitness test design `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`:
  · Detection logic (AST walk)
  · Bypass list (BYPASS_FILES + magic comment)
  · Failure message diagnostic
  · Performance budget <2s
  · Edge cases (mocker.patch, with patch.object, etc.)
- § 3 CLAUDE.md update (conditional rule trigger entry)
- § 4 Cross-link to PR-1 CONTRACT
- § 5 Open questions for PM
- § 6 Research Notes

Última línea:
<!-- @pm: CONTRACT.md PR-3 standalone ready. Próximo paso: ejecutar PR-3/prompts/02-builder-start.md -->
```
