# FP4 — Voseo cleanup amplio en 9 prompts remaining (B23.1-TP11)

**Bug origen:** TP11 J4 post-fix B23 → voseo residual en outputs. Pattern B23-TP11 fix solo cubrió 2 archivos (`deep_agent.py::_DEEP_AGENT_SUFFIX_ES` + `subagents/url_analyzer.py`).
**TP origen:** `results/TP11-2026-04-26.md §B23.1-TP11`.
**Tiempo estimado:** 4 horas.
**Pre-req hard:** TP11 cerrado (B23-TP11 commit `ed18daef` aplicado).
**Capa stack:** Backend (system prompts j2 templates + subagents + tools + observability).
**Paralelizable con FP1.**

---

## Misión

Aplicar el pattern B23-TP11 (compliance test + tuteo conversion) a los 9 archivos remanentes con voseo. Cuando termine, H4 tono PASS clean (de PARTIAL post-FP3 a PASS) + arch fitness ratchet "todos system prompts copilot module = 0 voseo" implementado.

---

## Research mandate

Queries:

- `"NLP register style transfer LLM system prompt 2026"` — best practice register consistency.
- `"regex word boundary unicode python re module 2026"` — confirma scanner accent-aware patterns.

(Research mínimo — pattern ya validado en B23-TP11. Solo confirmar Python re unicode behaviors no cambiaron.)

---

## Acceptance criteria

| AC | Descripción | Evidence pre-fix | Evidence post-fix |
|---|---|---|---|
| **AC1** | `infrastructure/prompts/templates/copilot_system_static.j2` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC2** | `infrastructure/prompts/templates/brand_summary_lighthouse.j2` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC3** | `application/orchestrator/subagents/data_query.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC4** | `application/tools/fetch_url.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC5** | `application/tools/pin_to_memory.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC6** | `application/tools/format_for_channel.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC7** | `application/tools/url_inspiration_analyzer.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC8** | `application/tools/ask_tenant_data/{synthesizer,tool}.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC9** | `application/observability/judge.py` 0 voseo tokens | grep voseo present | scanner test PASS |
| **AC10** | Arch fitness ratchet test: TODOS los `*.j2` + `subagents/*.py` + `tools/*.py` + `observability/*.py` del copilot module = 0 voseo. Allowlist allow-shrink-only. | n/a | new arch test PASS |
| **AC11** | Live re-run J4 audit + J2 URL inspiration (que pasan por subagents) → 0 voseo en outputs user-facing intermediate + final | residual voseo intermediate | 0 voseo end-to-end |

---

## Procedimiento

### Setup
- Reuse compliance test scanner pattern desde `backend/tests/modules/copilot/test_deep_agent_prompt_voseo_compliance.py` (B23-TP11). Extender o crear nuevo file por archivo target.

### AC1-AC9 — file-by-file conversion

Para cada archivo target:

1. **Test RED:** add test al test file que asserta `_scan_voseo(file_content) == []`. Para `*.j2` templates: load file content as string (no Jinja render); para `*.py` con prompts: import module + check string vars.
2. **Run grep para listar voseo tokens en el archivo:**
   ```bash
   grep -nE "anotá|marcá|avanzás|querés|tenés|podés|...|aprovechás|guardás|sugerís|llamá|reportá|continuá|devolvele" {file}
   ```
3. **Convert manual:** voseo → tuteo según glosario `.claude/rules/spanish-text.md`.
4. **GREEN:** test pasa.

### AC10 — arch fitness ratchet

Crear `backend/tests/architecture/test_copilot_prompts_voseo_compliance.py`:
```python
"""Arch fitness — todos system prompts del copilot module = 0 voseo."""

from pathlib import Path
import pytest
from tests.modules.copilot.test_deep_agent_prompt_voseo_compliance import _scan_voseo

COPILOT_PROMPTS_PATHS = [
    Path("src/modules/copilot/infrastructure/prompts/templates"),
    Path("src/modules/copilot/application/orchestrator/subagents"),
    Path("src/modules/copilot/application/tools"),
    Path("src/modules/copilot/application/observability"),
    Path("src/modules/copilot/application/orchestrator"),  # deep_agent.py
]

# Allowlist for files that legitimately CONTAIN voseo as data, e.g.
# output_sanitizer.py mapping keys. Allow-shrink-only.
KNOWN_VOSEO_ALLOWLIST = {
    "src/modules/copilot/application/orchestrator/output_sanitizer.py",  # voseo→tuteo mapping
    # No agregar más sin razón documentada en commit message.
}

@pytest.fixture
def all_prompt_files() -> list[Path]:
    files = []
    for base in COPILOT_PROMPTS_PATHS:
        files.extend(base.rglob("*.j2"))
        files.extend(base.rglob("*.py"))
    return [f for f in files if "__pycache__" not in str(f) and not f.name.startswith("test_")]

def test_no_voseo_in_copilot_prompts(all_prompt_files: list[Path]) -> None:
    """Ratchet allow-shrink-only. Cualquier voseo en prompts del copilot = fail."""
    failures: dict[str, list[str]] = {}
    for path in all_prompt_files:
        rel_path = str(path.relative_to(Path.cwd()))
        if rel_path in KNOWN_VOSEO_ALLOWLIST:
            continue
        content = path.read_text(encoding="utf-8")
        found = _scan_voseo(content)
        if found:
            failures[rel_path] = sorted(set(found))
    assert not failures, (
        f"Voseo detectado en {len(failures)} files: {failures}. "
        "Apply tuteo neutro LatAm (regla 11) — Kimi K2.6 arrastra el voseo del system prompt al output user-facing."
    )
```

### AC11 — live verification

1. Restart `api_dev` post-fix.
2. Re-run J4 audit prompt mismo de TP11.
3. Captura full panelEnd + scan voseo. **0 instances en intermediate + final.**
4. Re-run J2 URL inspiration prompt. **0 voseo.**

---

## Tests / archivos a crear / modificar

### Backend
- 9 prompt files convertir voseo → tuteo (listed AC1-AC9).
- `backend/tests/modules/copilot/test_deep_agent_prompt_voseo_compliance.py` (UPDATE — extender con per-file tests).
- `backend/tests/architecture/test_copilot_prompts_voseo_compliance.py` (NEW — arch fitness ratchet).

---

## Failure playbook

- **Templates `.j2` con Jinja syntax:** convertir voseo cuidadosamente NO romper Jinja blocks `{% %}` `{{ }}`.
- **`output_sanitizer.py` mapping keys (voseo→tuteo dict)**: legítimo, **NO convertir**. Add a `KNOWN_VOSEO_ALLOWLIST`.
- **Tests anteriores rompen:** verify regression suite post-fix. Si quality eval fails (judge dimension prompt cambió), iterar phrasing.

---

## Sub-bugs descubiertos durante FP4

> Append-only.

- (none yet)

---

## Output esperado

`results/FP4-{fecha}.md` con:
- AC1-AC11 checklist
- Files modified count (~9-10) + voseo tokens converted total count
- Arch fitness new test
- Live verification J4 + J2 evidence: 0 voseo en outputs
- Aprendizajes para FP2 (FP4 paraleliza con FP1, handoff a FP2)
- Handoff prompt en `prompts/FP2-start.md` (si FP1 también ya cerró + ambos paralelos terminaron juntos).

**Nota orden:** FP4 NO bloquea a FP1. Si Chris ejecuta secuencial (FP1 → FP4 → FP2 → FP3), FP4 close handoff = FP2. Si Chris ejecuta paralelo (FP1 || FP4), el último que cierre genera el handoff a FP2.
