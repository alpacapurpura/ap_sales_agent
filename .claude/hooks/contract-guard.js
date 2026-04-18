#!/usr/bin/env node

// PostToolUse hook. Reminds Claude when editing SSoT files (contracts,
// catalogs, registries) what regen/test command to run. Output is
// intentionally terse (≤2 lines per match) to minimize token cost.
// Silent on non-match.

const RULES = [
  {
    name: 'etl-contract',
    patterns: [
      /\/analytics\/infrastructure\/providers\/[^/]+\.py$/,
      /\/analytics\/infrastructure\/etl\/[^/]+\.py$/,
      /\/analytics\/application\/services\/etl_service\.py$/,
      /\/analytics\/workers\/(scheduler|tasks)\.py$/,
      /\/analytics\/domain\/extraction_contract\.py$/,
      /\/src\/workers\/settings\.py$/,
    ],
    msg: 'ETL SSoT touched. Run: `make extraction-contract && cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q` (rule: .claude/rules/etl-extraction-contract.md)',
  },
  {
    name: 'metric-catalog',
    patterns: [/\/analytics\/domain\/metric_catalog\.py$/],
    msg: 'metric_catalog.py edited. Run: `cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q` (verify catalog↔contract alignment).',
  },
  {
    name: 'offer-catalogs',
    patterns: [
      /\/offer\/domain\/(archetype|value_level|format)_catalog\.py$/,
      /\/shared\/domain\/expert_business_type\.py$/,
    ],
    msg: 'Offer catalog SSoT touched. Bump _CATALOG_VERSION in matching API + run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q` AND `cd frontend && npx vitest run src/__tests__/architecture/test-no-catalog-duplicates.test.ts` (rule: .claude/rules/offer-catalogs.md)',
  },
  {
    name: 'channel-registry',
    patterns: [/\/analytics\/application\/services\/channel_registry\.py$/],
    msg: 'channel_registry.py edited. Do NOT duplicate STAGE_CHANNEL_MAP / PROVIDER_TO_CHANNEL_TYPES in stage services (rule: .claude/rules/analytics-metrics.md).',
  },
  {
    name: 'copilot-registry',
    patterns: [/\/copilot\/domain\/module_registry\.py$/],
    msg: 'module_registry.py edited. New modules need a ModuleDescriptor entry (rule: .claude/rules/copilot-resilience.md).',
  },
];

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', () => resolve(''));
    // If no stdin (run manually), don't hang.
    setTimeout(() => resolve(data), 200);
  });
}

async function main() {
  const raw = await readStdin();
  if (!raw) process.exit(0);

  let data;
  try { data = JSON.parse(raw); } catch { process.exit(0); }

  if (!['Write', 'Edit', 'MultiEdit'].includes(data.tool_name)) process.exit(0);

  const filePath = data.tool_input?.file_path || data.tool_input?.path || '';
  if (!filePath) process.exit(0);

  for (const rule of RULES) {
    if (rule.patterns.some((p) => p.test(filePath))) {
      console.error(`[contract-guard:${rule.name}] ${rule.msg}`);
      process.exit(0);
    }
  }

  process.exit(0);
}

main();
