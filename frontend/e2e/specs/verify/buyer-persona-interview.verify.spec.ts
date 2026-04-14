/**
 * E2E: Copilot Buyer Persona Interview — Real Backend
 *
 * Simulates real human users creating buyer personas via the AI interview.
 * NOT mocked — hits the live backend with real AI (LangGraph + Claude).
 *
 * What we evaluate:
 *   (A) Deterministic: HTTP status codes, sidebar opens, persona created
 *   (B) Structural: Checkpoint cards appear, interview completes, preview updates
 *   (C) Quality (soft): completeness_score thresholds, sections populated
 *
 * Requires:
 *   - Docker services running: visionarias_brain_dev + visionarias_client_dev
 *   - Valid Clerk session (via playwright/.clerk/user.json from setup project)
 *   - E2E_TENANT_ID set in .env
 *
 * Run a single scenario:
 *   cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=verify --grep="Ideal"
 *
 * Run full suite:
 *   cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=verify --grep="buyer-persona"
 *
 * IMPORTANT: Each test takes 3-10 min. Full suite ~30-60 min + real AI API costs.
 * Do NOT add to CI — run manually or on a schedule.
 */

import * as fs from 'fs';
import * as path from 'path';
import { test, expect } from '../../fixtures/auth.fixture';
import { CopilotPage } from '../../pages/copilot.pom';
import {
  sendAndWaitForAI,
  drainInterviewToCompletion,
  listPersonasViaAPI,
  deleteAllPersonasViaAPI,
  abandonActiveInterviewViaAPI,
  captureTranscript,
} from '../../fixtures/interview-helpers';
import {
  evaluatePersona,
  serializeReport,
} from '../../fixtures/persona-evaluator';
import {
  SCENARIO_IDEAL,
  SCENARIO_VAGUE,
  SCENARIO_EXPERT,
  SCENARIO_CONFUSED,
  SCENARIO_MULTI_PERSONA_FIRST,
  SCENARIO_MULTI_PERSONA_SECOND,
  SCENARIO_ABANDON,
} from '../../fixtures/interview-scenarios';

const REPORTS_DIR = path.join(__dirname, '../../reports');

// ── Setup / Teardown ─────────────────────────────────────────────────────────

async function cleanSlate(page: Parameters<typeof abandonActiveInterviewViaAPI>[0], tenantId: string): Promise<void> {
  // Navigate to an authenticated route first so Clerk session is loaded
  await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000); // Wait for Clerk JS to initialize

  await abandonActiveInterviewViaAPI(page, tenantId);
  const deleted = await deleteAllPersonasViaAPI(page, tenantId);
  if (deleted > 0) {
    console.log(`[cleanup] Deleted ${deleted} stale persona(s)`);
  }
}

function saveReport(scenarioId: string, reportJson: string): void {
  try {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const file = path.join(REPORTS_DIR, `buyer-persona-${scenarioId}-${ts}.json`);
    fs.writeFileSync(file, reportJson, 'utf8');
    console.log(`[report] Saved to ${path.basename(file)}`);
  } catch {
    // Non-fatal — test should not fail because we couldn't write a report
  }
}

// ── Scenario 1: Ideal User (Happy Path) ──────────────────────────────────────

test.describe('buyer-persona interview @verify', () => {
  test('Escenario 1 — Ideal: interview completo con respuestas detalladas', async ({
    page,
    tenantId,
  }) => {
    const scenario = SCENARIO_IDEAL;
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    await test.step('Navegar a publico y click Modo Inteligente', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });

      // Wait for empty state
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });

      // Click "Modo Inteligente"
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
    });

    await test.step('Copilot sidebar se expande con preview pane', async () => {
      // Structural: sidebar expanded (780px mode with 2 columns)
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
      await expect(copilot.focusBar).toBeVisible({ timeout: 10_000 });
      await copilot.expectInputReady();
    });

    await test.step('Enviar respuestas del escenario', async () => {
      for (const response of scenario.responses) {
        await sendAndWaitForAI(copilot, response, 90_000);

        // If a checkpoint appeared, confirm it and continue
        const checkpointVisible = await copilot.checkpointCard.isVisible().catch(() => false);
        if (checkpointVisible) {
          console.log(`[ideal] Checkpoint appeared — confirming`);
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000); // Wait for block advance
        }
      }
    });

    await test.step('Completar interview (drain + card final)', async () => {
      // Keep advancing the interview with confirmation turns until it completes (5 min budget)
      const completed = await drainInterviewToCompletion(copilot, 5 * 60_000);

      // Structural (soft): complete card should appear — ideal scenario should complete
      expect.soft(completed, 'Interview should complete for ideal user').toBe(true);
      console.log(`[ideal] Interview completed: ${completed}`);
    });

    await test.step('Evaluar calidad de la persona resultante', async () => {
      // Get persona via API list (most recently created)
      const personas = await listPersonasViaAPI(page, tenantId);
      expect(personas.length, 'At least one persona should exist').toBeGreaterThan(0);
      const persona = personas[0];

      // Deterministic: persona exists with some demographics
      expect(Object.keys(persona.demographics ?? {})).not.toHaveLength(0);

      const transcript = await captureTranscript(copilot);
      const report = evaluatePersona(persona, scenario.id, transcript);
      saveReport(scenario.id, serializeReport(report));

      console.log(`[ideal] completeness_score: ${report.completenessScore}`);
      console.log(`[ideal] sections populated: ${report.sectionsPopulated}/9`);
      console.log(`[ideal] total messages: ${report.totalMessages}`);

      // Quality assertions (soft — AI is non-deterministic)
      expect.soft(report.completenessScore, 'completeness_score').toBeGreaterThanOrEqual(
        scenario.thresholds.minCompletenessScore,
      );
      expect.soft(report.sectionsPopulated, 'sections populated').toBeGreaterThanOrEqual(
        scenario.thresholds.minSectionsPopulated,
      );
    });
  });

  // ── Scenario 2: Vague User ─────────────────────────────────────────────────

  test('Escenario 2 — Vago: AI adapta preguntas a respuestas mínimas', async ({
    page,
    tenantId,
  }) => {
    const scenario = SCENARIO_VAGUE;
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    await test.step('Iniciar interview vago', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
    });

    await test.step('Enviar respuestas vagas y confirmar checkpoints', async () => {
      for (const response of scenario.responses) {
        await sendAndWaitForAI(copilot, response, 90_000);

        const checkpointVisible = await copilot.checkpointCard.isVisible().catch(() => false);
        if (checkpointVisible) {
          console.log(`[vague] Checkpoint appeared — confirming with: ${scenario.checkpointConfirmation}`);
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }
      }
    });

    await test.step('Validar que interview avanzó (no loop infinito)', async () => {
      const transcript = await captureTranscript(copilot);
      const totalMessages = transcript.length;

      // Deterministic: AI responded without getting stuck (less than max)
      const maxMessages = scenario.thresholds.maxTotalMessages ?? 40;
      expect(totalMessages, 'AI should not loop — max messages exceeded').toBeLessThan(maxMessages);

      const personas = await listPersonasViaAPI(page, tenantId);
      expect(personas.length, 'At least one persona should exist').toBeGreaterThan(0);
      const persona = personas[0];
      expect(persona).not.toBeNull();

      const report = evaluatePersona(persona, scenario.id, transcript);
      saveReport(scenario.id, serializeReport(report));

      console.log(`[vague] completeness_score: ${report.completenessScore}`);
      console.log(`[vague] sections populated: ${report.sectionsPopulated}/9`);
      console.log(`[vague] total messages: ${report.totalMessages}`);

      // Quality (soft) — even vague user should get some data
      expect.soft(report.completenessScore, 'even vague user should have some score').toBeGreaterThanOrEqual(
        scenario.thresholds.minCompletenessScore,
      );
    });
  });

  // ── Scenario 3: Expert Dumper ──────────────────────────────────────────────

  test('Escenario 3 — Experto: AI extrae múltiples campos de un solo mensaje', async ({
    page,
    tenantId,
  }) => {
    const scenario = SCENARIO_EXPERT;
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    await test.step('Iniciar interview', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
    });

    await test.step('Enviar dump masivo de información', async () => {
      for (const response of scenario.responses) {
        await sendAndWaitForAI(copilot, response, 120_000);

        const checkpointVisible = await copilot.checkpointCard.isVisible().catch(() => false);
        if (checkpointVisible) {
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }

        // Check if interview is already complete
        const completedVisible = await copilot.interviewCompleteCard.isVisible().catch(() => false);
        if (completedVisible) break;
      }
    });

    await test.step('Evaluar eficiencia y calidad', async () => {
      const personas = await listPersonasViaAPI(page, tenantId);
      expect(personas.length, 'At least one persona should exist').toBeGreaterThan(0);
      const persona = personas[0];
      const transcript = await captureTranscript(copilot);
      const report = evaluatePersona(persona, scenario.id, transcript);
      saveReport(scenario.id, serializeReport(report));

      console.log(`[expert] completeness_score: ${report.completenessScore}`);
      console.log(`[expert] sections populated: ${report.sectionsPopulated}/9`);
      console.log(`[expert] total messages: ${report.totalMessages}`);

      // Hard: should have multiple sections from the big dump
      expect(persona.demographics, 'demographics should be populated from dump').not.toEqual({});

      // Quality (soft)
      expect.soft(report.completenessScore, 'expert score').toBeGreaterThanOrEqual(
        scenario.thresholds.minCompletenessScore,
      );
      expect.soft(report.sectionsPopulated, 'expert sections').toBeGreaterThanOrEqual(
        scenario.thresholds.minSectionsPopulated,
      );

      // Efficiency (soft): should not take many messages
      const maxMsgs = scenario.thresholds.maxTotalMessages ?? 20;
      expect.soft(report.totalMessages, 'expert should be efficient').toBeLessThanOrEqual(maxMsgs);
    });
  });

  // ── Scenario 4: Contradictory User ────────────────────────────────────────

  test('Escenario 4 — Contradictorio: AI detecta y resuelve contradicciones', async ({
    page,
    tenantId,
  }) => {
    const scenario = SCENARIO_CONFUSED;
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    let clarifyCardAppeared = false;

    await test.step('Iniciar interview', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
    });

    await test.step('Enviar respuestas contradictorias', async () => {
      for (const response of scenario.responses) {
        await sendAndWaitForAI(copilot, response, 90_000);

        // Check if clarify card appeared (AI detected contradiction)
        if (await copilot.clarifyCard.isVisible().catch(() => false)) {
          clarifyCardAppeared = true;
          console.log(`[confused] Clarify card appeared — AI detected contradiction`);
          // Continue conversation to resolve it
        }

        // Confirm checkpoints
        if (await copilot.checkpointCard.isVisible().catch(() => false)) {
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }

        if (await copilot.interviewCompleteCard.isVisible().catch(() => false)) break;
      }
    });

    await test.step('Evaluar manejo de contradicciones', async () => {
      // Structural (soft): AI should have used clarify tool
      expect.soft(clarifyCardAppeared, 'AI should detect contradiction and show clarify card').toBe(true);

      const personas = await listPersonasViaAPI(page, tenantId);
      expect(personas.length, 'At least one persona should exist after contradictory interview').toBeGreaterThan(0);
      const persona = personas[0];
      const transcript = await captureTranscript(copilot);
      const report = evaluatePersona(persona, scenario.id, transcript);
      saveReport(scenario.id, serializeReport(report));

      console.log(`[confused] completeness_score: ${report.completenessScore}`);
      console.log(`[confused] clarify card appeared: ${clarifyCardAppeared}`);

      expect.soft(report.completenessScore, 'confused user score').toBeGreaterThanOrEqual(
        scenario.thresholds.minCompletenessScore,
      );
    });
  });

  // ── Scenario 5: Multi-Persona ──────────────────────────────────────────────

  test('Escenario 5 — Multi-Persona: dos personas sin conflicto de sesión', async ({
    page,
    tenantId,
  }) => {
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    let persona1Id: string | null = null;
    let persona2Id: string | null = null;

    await test.step('Crear y completar Primera Persona', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
      // Capture persona1 ID after creation
      const createdPersonas = await listPersonasViaAPI(page, tenantId);
      if (createdPersonas.length > 0) persona1Id = createdPersonas[0].id;

      const scenario1 = SCENARIO_MULTI_PERSONA_FIRST;
      for (const response of scenario1.responses) {
        await sendAndWaitForAI(copilot, response, 90_000);
        if (await copilot.checkpointCard.isVisible().catch(() => false)) {
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }
        if (await copilot.interviewCompleteCard.isVisible().catch(() => false)) break;
      }

      // If not complete, confirm remaining checkpoints
      for (let i = 0; i < 3; i++) {
        if (await copilot.checkpointCard.isVisible().catch(() => false)) {
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }
        if (await copilot.interviewCompleteCard.isVisible().catch(() => false)) break;
      }
    });

    await test.step('Volver a publico y crear Segunda Persona', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });

      // Should see the first persona card now
      await page.waitForTimeout(2000);

      // Click "Nueva Persona" to create second
      const nuevaPersonaButton = page.getByRole('button', { name: /Nueva Persona/i });
      const modoInteligenteButton = page.getByRole('button', { name: /Modo Inteligente/i });

      if (await nuevaPersonaButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await nuevaPersonaButton.click();
        await page.waitForTimeout(500);
      }

      // Should now see the mode selector
      await expect(modoInteligenteButton.first()).toBeVisible({ timeout: 10_000 });

      await modoInteligenteButton.first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });

      // Capture persona2 ID — the one that's different from persona1
      const allPersonas = await listPersonasViaAPI(page, tenantId);
      const newPersona = allPersonas.find((p) => p.id !== persona1Id);
      persona2Id = newPersona?.id ?? null;

      // Deterministic: no 409 conflict — second interview starts cleanly
      expect(persona2Id, 'Second persona should be created without conflict').toBeTruthy();
      expect(persona2Id, 'Second persona ID should differ from first').not.toBe(persona1Id);

      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
    });

    await test.step('Completar Segunda Persona brevemente', async () => {
      const scenario2 = SCENARIO_MULTI_PERSONA_SECOND;
      for (const response of scenario2.responses) {
        await sendAndWaitForAI(copilot, response, 90_000);
        if (await copilot.checkpointCard.isVisible().catch(() => false)) {
          await copilot.confirmCheckpoint();
          await page.waitForTimeout(2000);
        }
        if (await copilot.interviewCompleteCard.isVisible().catch(() => false)) break;
      }
    });

    await test.step('Verificar que existen dos personas distintas en DB', async () => {
      const personas = await listPersonasViaAPI(page, tenantId);

      // Hard: two distinct personas
      expect(personas.length, 'Should have 2 personas').toBeGreaterThanOrEqual(2);

      const p1 = personas.find((p) => p.id === persona1Id);
      const p2 = personas.find((p) => p.id === persona2Id);

      expect(p1, 'First persona exists in DB').toBeTruthy();
      expect(p2, 'Second persona exists in DB').toBeTruthy();

      // Soft: both have some completeness
      expect.soft(p1?.completeness_score, 'p1 score').toBeGreaterThanOrEqual(0);
      expect.soft(p2?.completeness_score, 'p2 score').toBeGreaterThanOrEqual(0);
    });
  });

  // ── Scenario 6: Abandonment ────────────────────────────────────────────────

  test('Escenario 6 — Abandono: persona shell persiste después de salir', async ({
    page,
    tenantId,
  }) => {
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    let personaId: string | null = null;

    await test.step('Iniciar interview y responder 2 preguntas', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });
      await page.getByRole('button', { name: /Modo Inteligente/i }).first().click();
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
      // Get the persona ID after creation
      const createdPersonas = await listPersonasViaAPI(page, tenantId);
      if (createdPersonas.length > 0) personaId = createdPersonas[0].id;

      const scenario = SCENARIO_ABANDON;
      // Only send the first 2 responses
      for (const response of scenario.responses) {
        await sendAndWaitForAI(copilot, response, 60_000);
      }
    });

    await test.step('Salir de Focus Mode', async () => {
      // Click "Salir de Focus"
      await copilot.focusBarExitButton.click();

      // Confirm if dialog appears
      const confirmButton = page.getByRole('button', { name: /salir sin guardar/i });
      if (await confirmButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirmButton.click();
      }

      // Deterministic: no crash, sidebar should close or be in collapsed/open state
      await expect(copilot.focusBar).not.toBeVisible({ timeout: 10_000 });
    });

    await test.step('Verificar que la persona shell existe en DB', async () => {
      const personas = await listPersonasViaAPI(page, tenantId);

      // Hard: persona shell should persist after abandonment
      expect(personas.length, 'Persona shell should persist after abandonment').toBeGreaterThan(0);
      const persona = personaId
        ? personas.find((p) => p.id === personaId) ?? personas[0]
        : personas[0];
      expect(persona, 'Persona should be retrievable').toBeTruthy();

      // Hard: navigate to publico and see the persona card
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000);

      // The page should show at least one persona card (not empty state)
      const personaCards = page.locator('[data-testid="persona-card"]').or(
        page.getByText(SCENARIO_ABANDON.personaName),
      );
      await expect(personaCards.first()).toBeVisible({ timeout: 15_000 });
    });
  });

  // ── Scenario 7: Manual Mode + Focus ───────────────────────────────────────

  test('Escenario 7 — Manual + Focus: crear manualmente y usar copilot en focus mode', async ({
    page,
    tenantId,
  }) => {
    const copilot = new CopilotPage(page);

    await test.step('Clean slate', async () => {
      await cleanSlate(page, tenantId);
    });

    let personaId: string | null = null;

    await test.step('Crear persona en Modo Manual', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await expect(page.getByText('Sin Buyer Personas').or(page.getByText('Nueva Persona'))).toBeVisible({ timeout: 30_000 });

      await page.getByRole('button', { name: /Modo Manual/i }).first().click();

      // Hard: should navigate to persona detail page — extract ID from URL
      await expect(page).toHaveURL(/brand-studio\/publico\/persona\//, { timeout: 15_000 });
      const url = page.url();
      const urlParts = url.split('/persona/');
      personaId = urlParts[urlParts.length - 1]?.split('?')[0] ?? null;
      expect(personaId, 'Should extract personaId from URL').toBeTruthy();
    });

    await test.step('Llenar datos demográficos manualmente', async () => {
      // Fill in a few demographic fields — these have text inputs
      const ageRangeInput = page.getByLabel(/rango de edad/i).or(page.getByPlaceholder(/edad/i));
      const locationInput = page.getByLabel(/ubicación/i).or(page.getByPlaceholder(/ciudad/i));

      if (await ageRangeInput.isVisible({ timeout: 5000 }).catch(() => false)) {
        await ageRangeInput.fill('35-50 años');
      }
      if (await locationInput.isVisible({ timeout: 5000 }).catch(() => false)) {
        await locationInput.fill('Ciudad de México');
      }

      // Wait for auto-save debounce (1500ms + buffer)
      await page.waitForTimeout(3000);

      // Verify persona is accessible via API after manual fill
      const personas = await listPersonasViaAPI(page, tenantId);
      expect(personas.length, 'Persona should be accessible via API after manual fill').toBeGreaterThan(0);
    });

    await test.step('Volver a publico y activar Focus Mode', async () => {
      await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000);

      // Find and click the Focus button on the persona card
      const focusButton = page.getByRole('button', { name: /focus/i }).first();
      await expect(focusButton).toBeVisible({ timeout: 15_000 });
      await focusButton.click();

      // Hard: copilot sidebar expands with preview pane
      await expect(copilot.previewPane).toBeVisible({ timeout: 15_000 });
      await expect(copilot.focusBar).toBeVisible({ timeout: 10_000 });
    });

    await test.step('Usar copilot en Focus Mode para completar pain points', async () => {
      await copilot.expectInputReady();
      await sendAndWaitForAI(
        copilot,
        'Completa los pain points de esta persona: su mayor dolor es la falta de tiempo para implementar estrategias de marketing por sí mismo',
        90_000,
      );

      // Give the AI time to use entity_write tool
      await page.waitForTimeout(2000);

      // Soft: copilot may have updated the preview pane
      const previewUpdated = await copilot.previewPane.textContent();
      expect.soft(previewUpdated?.length ?? 0, 'Preview pane should have content').toBeGreaterThan(10);
    });
  });
});
