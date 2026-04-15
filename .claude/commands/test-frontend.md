Run frontend quality gates + functional tests + health checks natively in WSL.
This is the DEFINITIVE frontend verification command. All steps must pass before committing.

**CRITICAL:** All tools run from `frontend/`. NEVER use `docker exec` for lint/tests/tsc.

## Execution: run ALL steps sequentially. Stop on first BLOCKER failure.

### Step 1: Verify tools
```bash
cd /home/chris/AISALESHT/frontend && npx tsc --version && npx vitest --version
```
If missing: `npm ci`

---

## QUALITY GATES (blockers — 0 errors required)

### Step 2: TypeScript strict (tsc)
```bash
cd /home/chris/AISALESHT/frontend && npx tsc --noEmit
```
Must produce 0 errors. `strict: true` in tsconfig.

### Step 3: ESLint (60+ rules, 0 errors)
```bash
cd /home/chris/AISALESHT/frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
```
**0 errors required.** Warnings are tracked but don't block.
After config changes: `rm -f .eslintcache` first.

Rules enforced as ERROR (will fail this step):
- `sonarjs/cognitive-complexity` (max 15)
- `max-depth` (max 4), `max-params` (max 4)
- `no-explicit-any`, `no-floating-promises`, `no-misused-promises`
- `boundaries/dependencies` (FSD enforcement)
- `no-debugger`, `no-eval`, `no-var`, `no-alert`, `no-empty`, `prefer-const`

Rules enforced as WARN (reported in health checks):
- `check-file/filename-naming-convention` — PascalCase components, kebab-case non-components
- `check-file/folder-naming-convention` — kebab-case folders
- `jsdoc/require-jsdoc` — exported functions need JSDoc
- `max-lines` (350), `max-lines-per-function` (100)
- `react-perf/*`, `sonarjs/*`, `import/order`

Count warnings by category for report:
```bash
./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache --format json 2>/dev/null | python3 -c "
import json,sys; d=json.load(sys.stdin)
cats={'check-file':0,'jsdoc':0,'react-perf':0,'sonarjs':0,'max-lines':0,'other':0}
for f in d:
  for m in f['messages']:
    if m['severity']!=1: continue
    r=m.get('ruleId','') or ''
    matched=False
    for k in cats:
      if k in r: cats[k]+=1; matched=True; break
    if not matched: cats['other']+=1
total=sum(cats.values())
[print(f'  {v:4} {k}') for k,v in sorted(cats.items(),key=lambda x:x[1],reverse=True)]
print(f'  TOTAL: {total}')
"
```

---

## FUNCTIONAL TESTS (blockers)

### Step 4: Unit tests with coverage (Vitest)
```bash
cd /home/chris/AISALESHT/frontend && npx vitest run --coverage
```
Coverage thresholds: **all 20%** (statements, branches, functions, lines).
Current: ~25%/21%/22%/25%. Test count: ~1063.

---

## HEALTH CHECKS (informational — report but don't block)

### Step 5: Code duplication (jscpd)
```bash
cd /home/chris/AISALESHT && npx jscpd frontend/src/ --threshold 5 --reporters console
```
Baseline: 4.52% (338 clones). TSX is highest at 5.29%.
If >5% total: **WARNING** — new duplication introduced.
If >8%: **CRITICAL** — must refactor before shipping.

### Step 6: Dead code (knip)
```bash
cd /home/chris/AISALESHT/frontend && npx knip 2>&1 | head -60
```
Config: `knip.config.ts`. Reports unused files, exports, dependencies.
⚠️ Known false positives: barrel spreads, Next.js routes, some devDeps.
Focus on: new unused files (not pre-existing), unused exports you just created.

### Step 7: Circular imports (madge)
```bash
cd /home/chris/AISALESHT/frontend && npx madge --circular src/ --extensions ts,tsx
```
Known: 2 cycles in offer-studio. Any NEW cycles: flag as WARNING.

### Step 8: Security audit (npm audit)
```bash
cd /home/chris/AISALESHT/frontend && npm audit --audit-level=high
```
Reports HIGH and CRITICAL vulnerabilities in npm dependencies.

---

## REPORT

Summarize as table:

| Gate | Step | Result | Details |
|------|------|--------|---------|
| QUALITY | TypeScript (tsc) | PASS/FAIL | 0 errors, strict mode |
| QUALITY | ESLint (60+ rules) | PASS/FAIL | 0 errors, N warnings |
| QUALITY | — check-file warnings | info | N naming violations |
| QUALITY | — jsdoc warnings | info | N undocumented exports |
| FUNCTIONAL | Tests (N passed) | PASS/FAIL | coverage: XX% (min 20%) |
| HEALTH | Duplication (jscpd) | X.XX% | baseline 4.52%, warn >5% |
| HEALTH | Dead code (knip) | N unused | focus on NEW unused only |
| HEALTH | Circular imports (madge) | N cycles | baseline 2, warn on new |
| HEALTH | Security (npm audit) | PASS/FAIL | N vulnerabilities |

**If all QUALITY + FUNCTIONAL pass:** "Frontend OK — safe to commit."
**If any QUALITY or FUNCTIONAL fail:** list failures with file:line. Fix before committing.
**If HEALTH checks degrade:** warn user, suggest fixes, but don't block.

### Warning trend tracking
Compare current warnings against baselines (2026-04-15):
- check-file: 323 (should decrease)
- jsdoc: 616 (should decrease)
- react-perf: ~1509 (should decrease)
- Total ESLint warnings: ~5863 (should decrease)

If total warnings INCREASED vs last run: flag which categories grew and why.
