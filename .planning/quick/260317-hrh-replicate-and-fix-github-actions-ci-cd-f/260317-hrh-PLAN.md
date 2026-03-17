---
phase: quick
plan: 260317-hrh
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [QUICK-CI-FIX]

must_haves:
  truths:
    - "npm run lint exits 0 inside frontend container"
    - "npm run test (vitest run) exits 0 inside frontend container"
    - "Both commands match what deploy-prod.yml quality-gates job runs"
  artifacts: []
  key_links: []
---

<objective>
Replicate the GitHub Actions CI/CD quality-gates frontend jobs locally inside the Docker dev container, identify any lint errors or test failures, and fix them so both `npm run lint` and `npm run test` pass cleanly.

Purpose: Ensure pushes to main will not fail the CI pipeline's frontend quality gates.
Output: Clean lint + test runs; any source files fixed to resolve errors.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.github/workflows/deploy-prod.yml (CI workflow — quality-gates job)
@frontend/package.json (lint and test scripts)
@frontend/Dockerfile (test target definition)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Run frontend lint and fix all ESLint errors</name>
  <files>Any frontend .ts/.tsx/.js/.jsx files that have lint errors</files>
  <action>
Run the exact same lint command that CI runs inside the dev container:

```
docker exec -t visionarias_client_dev npm run lint
```

This runs `eslint . --ext .ts,.tsx,.js,.jsx` which matches the CI step `docker run --rm visionarias/frontend-test:ci npm run lint`.

If errors are found:
1. First try auto-fix: `docker exec -t visionarias_client_dev npm run lint:fix`
2. For any remaining errors that cannot be auto-fixed, manually fix each file
3. Common issues to watch for: `@next/next/no-html-link-for-pages` (use Next.js Link), `@next/next/no-img-element` (use Next.js Image), `jsx-a11y/*` warnings treated as errors, unused imports, missing dependencies in useEffect
4. Re-run lint after fixes to confirm clean exit

Do NOT disable ESLint rules or add eslint-disable comments unless the rule is genuinely wrong for the specific case. Fix the actual code.
  </action>
  <verify>
    <automated>docker exec -t visionarias_client_dev npm run lint</automated>
  </verify>
  <done>ESLint exits 0 with no errors and no warnings-as-errors</done>
</task>

<task type="auto">
  <name>Task 2: Run frontend tests and fix any failures</name>
  <files>Any frontend test or source files causing test failures</files>
  <action>
Run the exact same test command that CI runs inside the dev container:

```
docker exec -t visionarias_client_dev npm run test
```

This runs `vitest run` which matches the CI step `docker run --rm visionarias/frontend-test:ci` (whose CMD is `npm run test`).

If tests fail:
1. Read each failure carefully — identify whether it is a broken test or broken source code
2. Fix source code if the test expectation is correct
3. Fix test if the expectation is stale (e.g., component renamed, prop changed)
4. For import errors: check that test mocks match current module exports
5. Re-run tests after fixes to confirm all pass

If vitest is not installed or has config issues, check `frontend/vitest.config.ts` and ensure the test environment (happy-dom or jsdom) is properly configured.
  </action>
  <verify>
    <automated>docker exec -t visionarias_client_dev npm run test</automated>
  </verify>
  <done>All vitest tests pass with exit code 0</done>
</task>

</tasks>

<verification>
Both commands exit 0, matching what the CI quality-gates job expects:
1. `docker exec -t visionarias_client_dev npm run lint` -- exits 0
2. `docker exec -t visionarias_client_dev npm run test` -- exits 0
</verification>

<success_criteria>
- Frontend lint passes with no errors inside Docker container
- Frontend tests pass with no failures inside Docker container
- Results match what GitHub Actions deploy-prod.yml quality-gates would produce
- Any fixed files are committed
</success_criteria>

<output>
After completion, create `.planning/quick/260317-hrh-replicate-and-fix-github-actions-ci-cd-f/260317-hrh-SUMMARY.md`
</output>
