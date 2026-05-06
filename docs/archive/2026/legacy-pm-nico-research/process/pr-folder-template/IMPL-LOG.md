# IMPL-LOG — PR-{N}-{slug}

> Owner: builders (`nicolify-backend` / `nicolify-frontend` / `nicolify-agentic`). Append-only durante implementación. Sirve como diario de decisiones implementación.

## Sesión {fecha} — {builder name}

### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (si aplica)
- `UI-SPEC.md` ✓ (si aplica)
- Skills módulo-específicos: `{brand-expert | offer-expert | copilot-expert | etc}` ✓

### Decisiones implementación
- {decisión técnica + razón. Ej: "Usé X helper en vez de implementar desde cero porque ya existía en shared/"}
- ...

### Sub-deliverables completados
- [ ] sub-1: ... (commit hash)
- [ ] sub-2: ... (commit hash)
- [ ] sub-3: ... (commit hash)

### Tests escritos
- `tests/.../test_x.py::test_y` — qué cubre
- ...

### Quality gates
- [ ] Ruff verde (BE) / ESLint verde (FE)
- [ ] Mypy verde (BE) / TSC verde (FE)
- [ ] Pytest verde (BE) / Vitest verde (FE)
- [ ] Arch fitness tests verde
- [ ] Migration idempotente verde (si aplica)

### Bloqueadores encontrados
- {bloqueador + cómo se resolvió o por qué se difirió}

### Decisiones diferidas durante implementación
- {Lo que apareció y NO se resolvió ahora}

### Surface real entregada
| Tipo | Path | Estado |
|---|---|---|
| ... | ... | ... |

### Commits
- `{hash}` — `{conventional commit message}`
- ...

---

<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-N builder done" para review. -->
