# T-2 Result — BE imports rewrite: brand + offer (Wave 1A)

## Status: AWAITING_CHRIS (Halt Trigger #1)

T-2 execution halted before codemod application. Reason: luana-core packages NOT installed in AISALESHT backend venv — applying the import rewrite without packages resolvable would violate delta=0 (catastrophic test collection failure).

## Halt Trigger Summary

**Trigger #1 raised:** luana-core packages missing from AISALESHT venv.

```
ModuleNotFoundError: No module named 'luana_core_brand_studio'
ModuleNotFoundError: No module named 'luana_core_offer_studio'
```

AISALESHT/backend/pyproject.toml has no `[project]` section — no luana-core deps declared.
luana-platform/nicolify/pyproject.toml has `dependencies = []` (stub — not configured).

## Pre-flight Baselines Captured

| Metric | Value |
|---|---|
| Files in src/modules/brand + offer | 176 |
| `from src.` imports in src/modules/brand + offer | 431 |
| `from src.` imports in tests/modules/brand + offer | 344 |
| `patch('src.')` mock paths in brand+offer tests | 23 |

(These are the targets to reach 0 after successful T-2 execution.)

## Acceptance Criteria Status

| ID | Description | Result |
|---|---|---|
| A1 | `grep "from src."` brand + offer = 0 | NOT RUN (codemod not applied — halted) |
| A2 | `grep "patch('src.')"` brand + offer tests = 0 | NOT RUN |
| A3 | pytest brand + offer GREEN | NOT RUN |
| A4 | Arch fitness GREEN (preserves 36/36 anchors, ratchet 22, FieldContract baselines) | NOT RUN |

## Halt Trigger #1 Detail

**Evidence:**
- `luana_core_brand_studio` not importable in AISALESHT venv
- `luana_core_offer_studio` not importable in AISALESHT venv
- No luana-core entries in AISALESHT/backend/pyproject.toml
- `luana-platform/nicolify/pyproject.toml` = stub with empty deps

**Root cause:** T-2 was spawned without first installing luana-core workspace deps in the AISALESHT backend venv. The architect §7 (03-arch-be.md) specifies nicolify/backend should have luana-core deps declared as workspace members — this setup step was not completed.

**3 mitigation options for Chris:**

**(A) Install luana-core in AISALESHT venv (quickest for T-2):**
```bash
cd /home/chris/luana-platform
uv pip install --editable core/luana-core-brand-studio --editable core/luana-core-offer-studio
# (+ all transitive luana-core packages to satisfy imports in brand+offer)
# Then re-run T-2 in AISALESHT/backend context
```
Risk: transitive dep conflicts possible; AISALESHT venv is ephemeral (pre-archive).

**(B) Create nicolify/backend workspace structure FIRST (correct architecture):**
```bash
# 1. Create luana-platform/nicolify/backend/pyproject.toml per arch §7.1
# 2. uv sync from luana-platform root → installs workspace deps
# 3. Move/copy AISALESHT brand+offer code to luana-platform/nicolify/backend/
# 4. Run T-2 codemod in new location
```
Risk: T-2 scope expands to include workspace setup (not in current ticket spec).

**(C) Apply codemod + defer test verification:**
```bash
# Apply codemod on AISALESHT (imports rewritten but not resolvable yet)
# Accept pytest failures until env setup complete (separate ticket pre-T-2-tests)
```
Risk: VIOLATES spec Scenario 1.1 grader (pytest exit 0 required) + D5 delta=0.

**Recommended:** Option A (install in AISALESHT venv for T-2 execution) if Chris confirms this is acceptable, then close T-2 in AISALESHT context before T-10 (workspace setup + git mv). OR: add pre-T-2 setup ticket to install workspace deps properly.

## Files Modified

None (halted pre-codemod).

## Commits

None (halted pre-commit).

## Next Steps (post-Chris ratify)

1. Chris selects mitigation option (A/B/C)
2. Builder-backend (Opus) resumes with chosen path
3. If Option A: `cd /home/chris/luana-platform && uv pip install --editable core/luana-core-brand-studio --editable core/luana-core-offer-studio [+ transitive deps] && cd /home/chris/AISALESHT/backend && python scripts/codemod_be_imports.py --package=brand --apply && python scripts/codemod_be_imports.py --package=offer --apply`
4. Verify grep counts → 0 + pytest → exit 0 + arch fitness → GREEN
5. Single commit (T-2) + push
