# Prompt — Auditor kickoff (PR-3)

> Auditor: `nicolify-backend-auditor` (Opus)
> Lo spawnea el builder en Phase 2.2.

## Spawn pattern

```
Agent({
  description: "Audit PR-3 anti-default-flip",
  subagent_type: "nicolify-backend-auditor",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos `nicolify-backend-auditor` (Opus). Review READ-ONLY de PR-3 (anti-default-flip enforcement).

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Lectura obligatoria:
1. {pr_folder}/PR.md
2. {pr_folder}/CONTRACT.md
3. {pr_folder}/IMPL-LOG.md
4. gate-output.json
5. git diff main..HEAD del PR-3

Scope check:
- Si diff toca paths fuera scope (`.claude/rules/`, `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`, CLAUDE.md) → flag CROSS-SCOPE.

Verdict gate:
- gate-output.json overall.any_fail = true → FAIL automático.

Categorías review:
1. Rule documentation quality:
   - 4 steps mandatory documentados claramente
   - Inventario flags side-effect completo
   - Anti-patterns explícitos
   - Enforcement layers tabla completa
   - Penalizaciones documentadas
2. Arch fitness test correctness:
   - AST walk maneja edge cases (mocker.patch, with patch.object, decorators chain)
   - Bypass mechanism funciona (test del test)
   - Failure message diagnostic claro + linkea regla
   - False positives mínimos
   - Performance <2s validated
3. CLAUDE.md update consistency con tabla existing
4. Cross-link PR-1 CONTRACT (referenciado correctamente)
5. Tests del test (meta-test bypass) presentes
6. Anti-duplication.md no fue duplicado (referenciado, no copy-paste)

Findings niveles:
- FAIL: arch fitness no detecta mock targets básicos · bypass falla · performance >5s · regla missing 4 steps · duplicación con anti-duplication.md
- WARN: false positives detectables · failure message no linkea regla · CLAUDE.md inconsistencia menor
- info: typos · wording mejoras

Output: REVIEW.md con tabla gates, tabla 6 cats P/W/F, findings file:line, verdict mecánico.

Última línea:
<!-- @pm: REVIEW.md ready (verdict={PASS|WARN|FAIL}). Próximo paso: fix-loop iter-N+1 o /pm "PR-3 cerrar". -->

[BLOQUE VARIABLE]

Surface: business + meta (rules + arch fitness)
PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement
Iter actual: 1
gate-output.json esperado: {pr_folder}/gate-output.json
```
