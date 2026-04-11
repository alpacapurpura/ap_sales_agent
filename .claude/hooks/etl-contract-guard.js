#!/usr/bin/env node

/**
 * PostToolUse hook: After Edit/Write/MultiEdit on any analytics ETL file,
 * remind Claude to update the extraction contract + regenerate the Markdown
 * + run the architecture test.
 *
 * The contract is the single source of truth for what the ETL extracts.
 * Drift between the code and the contract is forbidden — see
 * .claude/rules/etl-extraction-contract.md.
 *
 * Trigger paths (any one):
 *   backend/src/modules/analytics/infrastructure/providers/*.py
 *   backend/src/modules/analytics/infrastructure/etl/*.py
 *   backend/src/modules/analytics/application/services/etl_service.py
 *   backend/src/modules/analytics/workers/scheduler.py
 *   backend/src/modules/analytics/workers/tasks.py
 *   backend/src/modules/analytics/domain/metric_catalog.py
 *   backend/src/modules/analytics/domain/extraction_contract.py
 *   backend/src/workers/settings.py
 *
 * Output: writes a reminder to stdout (visible in conversation as a system
 * notification). Always exits 0 — non-blocking by design.
 */

const TRIGGER_PATTERNS = [
  /\/analytics\/infrastructure\/providers\/[^/]+\.py$/,
  /\/analytics\/infrastructure\/etl\/[^/]+\.py$/,
  /\/analytics\/application\/services\/etl_service\.py$/,
  /\/analytics\/workers\/(scheduler|tasks)\.py$/,
  /\/analytics\/domain\/(metric_catalog|extraction_contract)\.py$/,
  /\/src\/workers\/settings\.py$/,
];

function reminder(filePath) {
  const isContract = filePath.endsWith('extraction_contract.py');
  const isCatalog = filePath.endsWith('metric_catalog.py');
  const isMarkdown = filePath.endsWith('extraction-contract.md');

  const lines = [
    '',
    '⚠️  ETL CONTRACT REMINDER',
    '──────────────────────────────────────────────────────────',
    `Edited: ${filePath}`,
    '',
    'You just touched a file that participates in the analytics ETL.',
    'Per .claude/rules/etl-extraction-contract.md, the FINAL STEP of any',
    'ETL change is mandatory:',
    '',
  ];

  if (isMarkdown) {
    lines.push(
      '  ❌ DO NOT edit docs/etl/extraction-contract.md by hand.',
      '     Edit backend/src/modules/analytics/domain/extraction_contract.py',
      '     and regenerate with `make extraction-contract`.',
    );
  } else if (isContract) {
    lines.push(
      '  1. Run `make extraction-contract` to regenerate',
      '     docs/etl/extraction-contract.md (the user-facing markdown).',
      '  2. Run `cd backend && .venv/bin/pytest',
      '     tests/architecture/test_extraction_contract.py -x -q`',
      '     to verify the contract is internally consistent.',
      '  3. Commit BOTH the .py source and the regenerated .md together.',
    );
  } else {
    lines.push(
      '  1. Update the matching entry in',
      '     backend/src/modules/analytics/domain/extraction_contract.py',
      '     (add MetricMapping / ChannelOutput / known_issue / bump',
      '     last_verified — whatever the change implies).',
      '  2. Run `make extraction-contract` to regenerate the markdown.',
      '  3. Run `cd backend && .venv/bin/pytest',
      '     tests/architecture/test_extraction_contract.py -x -q`.',
      '  4. Commit the provider change + contract update + regenerated',
      '     markdown TOGETHER in a single commit.',
    );
  }

  if (isCatalog) {
    lines.push(
      '',
      '  Catalog-specific note: every metric whose `providers` tuple lists',
      '  X must appear in X\'s ChannelOutput in the contract, OR be in',
      '  KNOWN_CATALOG_CONTRACT_GAPS in the test file with a justification.',
    );
  }

  lines.push(
    '',
    'Reminder docs:',
    '  - Rule:     .claude/rules/etl-extraction-contract.md',
    '  - Contract: backend/src/modules/analytics/domain/extraction_contract.py',
    '  - Markdown: docs/etl/extraction-contract.md',
    '  - Test:     backend/tests/architecture/test_extraction_contract.py',
    '──────────────────────────────────────────────────────────',
    '',
  );

  return lines.join('\n');
}

function main() {
  const input = process.argv[2];
  if (!input) process.exit(0);

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const tool = data.tool_name;
  if (!['Write', 'Edit', 'MultiEdit'].includes(tool)) process.exit(0);

  const filePath = data.tool_input?.file_path || data.tool_input?.path || '';
  if (!filePath) process.exit(0);

  for (const pattern of TRIGGER_PATTERNS) {
    if (pattern.test(filePath)) {
      // PostToolUse hooks emit reminders via stderr; Claude Code surfaces
      // them as system messages without blocking the operation.
      console.error(reminder(filePath));
      process.exit(0);
    }
  }

  process.exit(0);
}

main();
