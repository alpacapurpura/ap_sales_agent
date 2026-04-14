/**
 * Post-run evaluation script for buyer persona interview E2E tests.
 *
 * Reads JSON reports from frontend/e2e/reports/ and prints a summary table
 * comparing quality metrics across scenarios.
 *
 * Usage:
 *   cd /home/chris/AISALESHT && npx tsx scripts/evaluate-bp-interviews.ts
 *
 * Run after:
 *   cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=verify --grep="buyer-persona"
 */

import * as fs from 'fs';
import * as path from 'path';

const REPORTS_DIR = path.join(__dirname, '../frontend/e2e/reports');

interface CompletenessReport {
  personaId: string;
  scenario: string;
  completenessScore: number;
  hasDemographics: boolean;
  hasPsychographics: boolean;
  hasPainPoints: boolean;
  hasDesires: boolean;
  hasObjections: boolean;
  hasChannels: boolean;
  hasBuyerJourney: boolean;
  hasPurchaseTriggers: boolean;
  hasAntiPatterns: boolean;
  sectionsPopulated: number;
  totalMessages: number;
  transcript: Array<{ role: string; text: string }>;
  timestamp: string;
}

function readReports(): CompletenessReport[] {
  if (!fs.existsSync(REPORTS_DIR)) {
    console.error(`❌ Reports directory not found: ${REPORTS_DIR}`);
    console.error('   Run the E2E tests first:');
    console.error('   cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=verify --grep="buyer-persona"');
    process.exit(1);
  }

  const files = fs.readdirSync(REPORTS_DIR)
    .filter((f) => f.startsWith('buyer-persona-') && f.endsWith('.json'))
    .map((f) => path.join(REPORTS_DIR, f))
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs); // newest first

  if (files.length === 0) {
    console.error('❌ No buyer-persona report files found in', REPORTS_DIR);
    process.exit(1);
  }

  const reports: CompletenessReport[] = [];
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, 'utf8');
      reports.push(JSON.parse(content) as CompletenessReport);
    } catch {
      console.warn(`⚠️  Could not parse ${path.basename(file)}`);
    }
  }

  return reports;
}

function formatBool(v: boolean): string {
  return v ? '✅' : '❌';
}

function printTable(reports: CompletenessReport[]): void {
  const SCENARIO_ORDER = ['ideal', 'vague', 'expert', 'confused', 'multi-p1', 'multi-p2', 'abandon'];

  // Group by scenario, keep latest per scenario
  const byScenario = new Map<string, CompletenessReport>();
  for (const r of reports) {
    if (!byScenario.has(r.scenario)) {
      byScenario.set(r.scenario, r);
    }
  }

  const ordered = SCENARIO_ORDER
    .map((id) => byScenario.get(id))
    .filter((r): r is CompletenessReport => r !== undefined);

  // Add any scenarios not in the order list
  for (const [id, r] of byScenario) {
    if (!SCENARIO_ORDER.includes(id)) ordered.push(r);
  }

  console.log('\n═══════════════════════════════════════════════════════════════════');
  console.log('  BUYER PERSONA INTERVIEW — Quality Report');
  console.log(`  ${ordered.length} scenario(s), ${reports.length} total report(s)`);
  console.log('═══════════════════════════════════════════════════════════════════\n');

  console.log(
    '│ Scenario      │ Score │ Sections │ Demo │ Psycho │ Pain │ Desire │ Obj │ Ch │ BJ │ Msgs │',
  );
  console.log(
    '├───────────────┼───────┼──────────┼──────┼────────┼──────┼────────┼─────┼────┼────┼──────┤',
  );

  for (const r of ordered) {
    const scoreColor = r.completenessScore >= 50 ? '🟢' : r.completenessScore >= 20 ? '🟡' : '🔴';
    const id = r.scenario.padEnd(13).slice(0, 13);
    const score = `${scoreColor}${String(Math.round(r.completenessScore)).padStart(3)}%`;
    const sections = `${r.sectionsPopulated}/9`.padStart(8);

    console.log(
      `│ ${id} │ ${score} │${sections} │  ${formatBool(r.hasDemographics)}  │   ${formatBool(r.hasPsychographics)}  │  ${formatBool(r.hasPainPoints)}  │   ${formatBool(r.hasDesires)}  │  ${formatBool(r.hasObjections)} │ ${formatBool(r.hasChannels)} │ ${formatBool(r.hasBuyerJourney)} │ ${String(r.totalMessages).padStart(4)} │`,
    );
  }

  console.log('\n');

  // Flags
  const flags: string[] = [];
  for (const r of ordered) {
    if (r.completenessScore === 0 && r.scenario !== 'abandon') {
      flags.push(`🚨 ${r.scenario}: completeness_score = 0 — extract_structured may be broken`);
    }
    if (r.sectionsPopulated === 0 && r.scenario !== 'abandon') {
      flags.push(`🚨 ${r.scenario}: no sections populated — AI extraction not working`);
    }
    if (r.scenario === 'expert' && r.totalMessages > 15) {
      flags.push(`⚠️  ${r.scenario}: ${r.totalMessages} messages (expected < 15 for expert dumper)`);
    }
  }

  if (flags.length > 0) {
    console.log('🔍 QUALITY FLAGS:');
    for (const flag of flags) {
      console.log(`   ${flag}`);
    }
    console.log('');
  }

  // Transcript highlights
  console.log('📝 TRANSCRIPT HIGHLIGHTS (first 2 AI messages per scenario):');
  for (const r of ordered) {
    const aiMessages = r.transcript.filter((m) => m.role === 'assistant').slice(0, 2);
    if (aiMessages.length > 0) {
      console.log(`\n  [${r.scenario}]`);
      for (const msg of aiMessages) {
        console.log(`  AI: "${msg.text.slice(0, 100)}${msg.text.length > 100 ? '...' : ''}"`);
      }
    }
  }

  console.log('\n═══════════════════════════════════════════════════════════════════\n');
}

function main(): void {
  const reports = readReports();
  printTable(reports);
  console.log(`✅ Evaluated ${reports.length} report(s) from ${REPORTS_DIR}`);
}

main();
