# T-2 Implementation Log — PII Scanner + Pre-commit hook Section 8 + .eval-whitelist

story_id: eval-foundation-tenant-seed-data
ticket: T-2
builder: claude-sonnet-4-6 (builder-backend)
started_at: 2026-05-06T23:05Z
closed_at: 2026-05-07T00:30Z (approx)

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `tessl__pytest-api-testing` | test_seed_pii_scanner.py — subprocess.run patterns, tmp_path fixture, parametrize adversarial cases | Used `subprocess.run(..., check=False)` + `# noqa: S603`; `tmp_path` for adversarial YAMLs per "NO commit fixtures with real PII" |
| `backend-expert` (runtime-quality-checklist) | Pre-implementation anti-pattern check; standalone script no src/ imports | Confirmed AD5: scanner standalone — stdlib + PyYAML only. AD9: zero production_code impact |

---

## Iteration Log

### Iter 1 — TDD RED phase
Wrote tests first:
- `test_seed_pii_scanner.py` — 4 test functions (parametrized adversarial + whitelist + no PII in committed seeds)
- `test_pre_commit_hook.py::test_blocks_pii_in_seed_tenants` extended
All failed RED (scanner not yet created).

### Iter 2 — GREEN phase: scanner implementation
Wrote `backend/scripts/scan_seed_pii.py`:
- 9 regex patterns (email, phone_intl, dni_ar, cuit_ar, rut_cl, dni_pe, curp_mx, rfc_mx, url_internal_nicolify)
- DNI-PE context guards: `(?<![=:#/\d])(?<!\bid=)(?<!\brev=)(?<!\bver=)` to reduce false positives
- `_find_whitelist()` walks up max 6 levels from scan target
- Whitelist matching per pattern type (email domain, phone prefix, URL fragment)
- Exit codes 0 (clean), 1 (PII), 2 (error)

### Iter 3 — Bug fix: path double-nesting
Initial `test_seed_pii_scanner.py` used `parents[4]` expecting `backend/` BUT THEN appended `"backend" / "scripts"` → resolved to `backend/backend/scripts/`. Fixed: used `BACKEND_ROOT = parents[4]` (already at `backend/`) + `SCANNER = BACKEND_ROOT / "scripts" / "scan_seed_pii.py"`.

### Iter 4 — Bug fix: whitelist tests (exit 1 instead of 0)
`test_whitelist_skips_known_public_urls` and `test_whitelist_skips_synthetic_fixtures_in_sample_exchanges` failed because scanner walked upward from `tmp_path/clean/` but `.eval-whitelist` only existed in real `TENANTS_DIR`, not in `tmp_path`. Fix: `shutil.copy(str(WHITELIST_PATH), str(clean_dir / ".eval-whitelist"))` in each whitelist test.

### Iter 5 — Bug fix: hook test Scenario 2 (PII still on disk)
After `git restore --staged` in Scenario 1, the PII YAML was no longer staged but still existed on disk. Scanner scans ALL yaml files in directory (not just staged), so it still detected PII in Scenario 2. Fix: added `pii_yaml_file.unlink()` after unstage + before Scenario 2.

### Iter 6 — Ruff fix: S603, S607 noqa
`subprocess.run` calls without `check=True` triggered S603. Added `# noqa: S603` on all 4 subprocess calls. Initial `# noqa: S603, S607` had unused S607 tag — fixed with `ruff --fix`.

### Iter 7 — Pre-commit hook section number correction
CONTRACT/06-tickets.yaml says "Section 7" but reading the actual hook file revealed 7 sections already existed (Sections 1-7 including the checkpoint state enum validator added 2026-05-06). Section added as **Section 8** (not Section 7 as stated in task). PII scan logic only activates when staged files match `backend/tests/fixtures/eval/tenants/.*\.yaml$`.

---

## Files Created

| File | Type | Lines |
|---|---|---|
| `backend/scripts/scan_seed_pii.py` | NEW | 293 |
| `backend/tests/fixtures/eval/tenants/.eval-whitelist` | NEW | 20 |
| `backend/tests/fixtures/eval/tenants/test_seed_pii_scanner.py` | NEW | 181 |

## Files Modified

| File | Change |
|---|---|
| `scripts/git-hooks/pre-commit` | Added Section 8 (PII scan) before `exit 0` |
| `backend/tests/scripts/test_pre_commit_hook.py` | Added `test_blocks_pii_in_seed_tenants` function |

---

## Cross-module reads
None.

---

## Default-flip pre-audit
Not applicable — no `core/config.py` defaults touched.

---

## Test Output (final)

```
tests/scripts/test_pre_commit_hook.py::test_blocks_pii_in_seed_tenants PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_no_pii_in_committed_seeds PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_whitelist_skips_known_public_urls PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures[phone_intl] PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures[email] PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_whitelist_skips_synthetic_fixtures_in_sample_exchanges PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures[id_docs_cuit_ar] PASSED
tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures[url_internal_nicolify] PASSED

20 passed, 1 warning (combined test_seed_pii_scanner + test_pre_commit_hook)
Arch fitness: 827 passed, 1 warning
Ruff check: All checks passed
Ruff format: 9 files already formatted
```

---

## Validators T-2 status

| Acceptance criterion | Status |
|---|---|
| A1 — scanner detects 4 PII categories adversarial | GREEN (4/4) |
| A2 — whitelist skips known URLs + synthetic phones/emails | GREEN (2/2) |
| A3 — hook Section 8 blocks PII commit + message | GREEN (1/1) |
| A4 — zero backend/src/ or frontend/src/ modified | GREEN |

---

## Decisions honored
- AD5: scanner standalone (no `backend/src/` imports)
- AD9: zero production_code impact (scripts/ + tests/ + hooks only)
- Q5: PII concept confirmed (regex scan on staged seed YAMLs, not in-memory)
- parallel-safety M1: exact file staging by name
- tdd-mandatory: tests RED before implementation
