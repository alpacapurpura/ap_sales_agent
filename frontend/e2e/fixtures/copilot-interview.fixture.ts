import { type Page } from '@playwright/test';
import {
  type StartInterviewResponse,
  type ActiveInterviewResponse,
  type InterviewStateResponse,
} from '@/features/copilot/api/interview-api';

// ── Static mock data ──────────────────────────────────────────────────────────

/** Mock session returned by POST /api/v1/copilot/interview/start */
export const INTERVIEW_START_MOCK: StartInterviewResponse = {
  session_id: 'sess-mock-brand-001',
  conversation_id: 'conv-interview-001',
  config: {
    domain: 'brand',
    total_blocks: 4,
    blocks: ['identidad', 'audiencia', 'propuesta', 'comunicacion'],
  },
  initial_message:
    '¡Hola! Voy a ayudarte a definir tu marca. Empecemos por tu identidad. ¿Cómo describirías tu negocio en una frase?',
};

/** Mock response returned by POST /api/v1/copilot/interview/start for the "offer" domain */
export const INTERVIEW_START_OFFER_MOCK: StartInterviewResponse = {
  session_id: 'sess-mock-offer-001',
  conversation_id: 'conv-interview-offer-001',
  config: {
    domain: 'offer',
    total_blocks: 3,
    blocks: ['propuesta_valor', 'precio', 'entregables'],
  },
  initial_message:
    'Vamos a construir tu oferta. ¿Cuál es el problema principal que resuelves para tus clientes?',
};

/** Mock active interview (GET /api/v1/copilot/interview/active or resume response) */
export const INTERVIEW_ACTIVE_MOCK: ActiveInterviewResponse = {
  session_id: 'sess-mock-brand-001',
  domain: 'brand',
  domain_label: 'Marca',
  bloque_actual: 'audiencia',
  bloques_completados: ['identidad'],
  total_bloques: 4,
};

/** Mock state for an in-progress interview (GET /api/v1/copilot/interview/{id}/state) */
export const INTERVIEW_STATE_MOCK: InterviewStateResponse = {
  session_id: 'sess-mock-brand-001',
  mapa_global: {
    'identidad.nombre_negocio': 'Visionarias',
    'identidad.descripcion': 'Formación para emprendedoras con propósito',
  },
  bloque_actual: 'audiencia',
  bloques_completados: ['identidad'],
  config: {
    domain: 'brand',
    total_blocks: 4,
    blocks: ['identidad', 'audiencia', 'propuesta', 'comunicacion'],
  },
  messages_count: 8,
};

/** Mock for a completed interview (all blocks done). */
export const INTERVIEW_COMPLETED_STATE_MOCK: InterviewStateResponse = {
  ...INTERVIEW_STATE_MOCK,
  bloque_actual: '',
  bloques_completados: ['identidad', 'audiencia', 'propuesta', 'comunicacion'],
  messages_count: 32,
};

// ── Route mock setup ──────────────────────────────────────────────────────────

export interface InterviewMockOptions {
  /** Override the start response. Defaults to INTERVIEW_START_MOCK. */
  startResponse?: StartInterviewResponse;
  /** Override the active interview response. Pass null to simulate no active session (204). */
  activeResponse?: ActiveInterviewResponse | null;
  /** Override the state response. Defaults to INTERVIEW_STATE_MOCK. */
  stateResponse?: InterviewStateResponse;
  /** If true, the start endpoint returns 500 to test error handling. */
  startError?: boolean;
}

/**
 * Intercept all copilot interview endpoints with deterministic mock data.
 *
 * Endpoints mocked:
 *   POST /api/v1/copilot/interview/start
 *   GET  /api/v1/copilot/interview/active
 *   GET  /api/v1/copilot/interview/{sessionId}/state
 *   POST /api/v1/copilot/interview/{sessionId}/pause
 *   POST /api/v1/copilot/interview/{sessionId}/abandon
 */
export async function setupInterviewMocks(
  page: Page,
  options: InterviewMockOptions = {},
) {
  const startResponse = options.startResponse ?? INTERVIEW_START_MOCK;
  const activeResponse =
    options.activeResponse !== undefined
      ? options.activeResponse
      : INTERVIEW_ACTIVE_MOCK;
  const stateResponse = options.stateResponse ?? INTERVIEW_STATE_MOCK;

  // POST /interview/start
  await page.route('**/api/v1/copilot/interview/start', async (route) => {
    if (options.startError) {
      await route.fulfill({ status: 500, body: 'Internal Server Error' });
      return;
    }
    await route.fulfill({ json: startResponse, status: 200 });
  });

  // GET /interview/active
  await page.route('**/api/v1/copilot/interview/active', async (route) => {
    if (activeResponse === null) {
      // No active session — backend returns 204 No Content
      await route.fulfill({ status: 204 });
    } else {
      await route.fulfill({ json: activeResponse, status: 200 });
    }
  });

  // GET /interview/{sessionId}/state  (matches any session ID)
  await page.route('**/api/v1/copilot/interview/*/state', async (route) => {
    await route.fulfill({ json: stateResponse, status: 200 });
  });

  // POST /interview/{sessionId}/pause
  await page.route('**/api/v1/copilot/interview/*/pause', async (route) => {
    await route.fulfill({ status: 200, json: { ok: true } });
  });

  // POST /interview/{sessionId}/abandon
  await page.route('**/api/v1/copilot/interview/*/abandon', async (route) => {
    await route.fulfill({ status: 200, json: { ok: true } });
  });
}

/**
 * Full copilot interview setup — includes both interview endpoint mocks and
 * the chat stream mock so the interview conversation can proceed.
 *
 * Import copilot-chat.fixture.ts separately for fine-grained chat control.
 */
export async function setupInterviewFullMocks(
  page: Page,
  options: InterviewMockOptions = {},
) {
  await setupInterviewMocks(page, options);

  // Also mock the chat endpoint so interview messages stream correctly
  const { setupCopilotChatMocks } = await import('./copilot-chat.fixture');
  await setupCopilotChatMocks(page, {
    textChunks: [options.startResponse?.initial_message ?? INTERVIEW_START_MOCK.initial_message],
    conversationId: options.startResponse?.conversation_id ?? INTERVIEW_START_MOCK.conversation_id,
  });
}

// ── Helper: build checkpoint card mock data ───────────────────────────────────

/**
 * Build a mock SSE text_chunk that contains a checkpoint_card JSON payload.
 *
 * The copilot backend signals a checkpoint via a `ui_action` SSE event with
 * `action_type: "interview_checkpoint"`. Use buildCheckpointSSEBody from
 * copilot-chat.fixture.ts `buildChatSSEBodyWithTool` to combine this with
 * the streaming flow, or send it directly via a custom route.
 */
export function buildCheckpointUIAction(options: {
  blockId?: string;
  blockLabel?: string;
  summary?: Record<string, string>;
  healthScore?: number;
  blocksCompleted?: number;
  totalBlocks?: number;
}) {
  return {
    action_type: 'interview_checkpoint',
    block_id: options.blockId ?? 'identidad',
    block_label: options.blockLabel ?? 'Identidad de Marca',
    summary: options.summary ?? {
      'identidad.nombre_negocio': 'Visionarias',
      'identidad.descripcion': 'Formación para emprendedoras con propósito',
    },
    health_score: options.healthScore ?? 75,
    blocks_progress: {
      completed: options.blocksCompleted ?? 1,
      total: options.totalBlocks ?? 4,
    },
  };
}
