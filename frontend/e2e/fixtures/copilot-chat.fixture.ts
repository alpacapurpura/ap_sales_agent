import { type Page } from '@playwright/test';

// ── SSE helper ───────────────────────────────────────────────────────────────

/**
 * Build a valid SSE event string for Playwright's route.fulfill().
 * Each event follows the SSE wire format:
 *   event: <type>\ndata: <json>\n\n
 */
function sseEvent(event: string, data: Record<string, unknown>): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

/**
 * Build a complete, minimal SSE response body simulating a copilot chat stream.
 *
 * Default sequence:
 *   status(thinking) → text_chunk × N → done
 */
function buildChatSSEBody(options: {
  textChunks?: string[];
  conversationId?: string;
}): string {
  const chunks = options.textChunks ?? ['Hola, ', 'soy tu Copilot.'];
  const conversationId = options.conversationId ?? 'conv-mock-001';

  const parts: string[] = [
    sseEvent('status', { state: 'thinking' }),
    ...chunks.map((c) => sseEvent('text_chunk', { content: c })),
    sseEvent('done', { conversation_id: conversationId }),
  ];

  return parts.join('');
}

// ── Mock payloads ─────────────────────────────────────────────────────────────

/** Minimal successful chat stream. */
export const CHAT_MOCK_SIMPLE = {
  textChunks: ['Hola, soy tu Copilot. ¿En qué te puedo ayudar hoy?'],
  conversationId: 'conv-mock-001',
};

/** Multi-chunk stream simulating a longer assistant reply. */
export const CHAT_MOCK_LONG_REPLY = {
  textChunks: [
    'Tu marca es ',
    'el puente entre ',
    'quién eres y ',
    'a quién ayudas.',
  ],
  conversationId: 'conv-mock-002',
};

/** Stream that includes a tool_start + tool_result event before the reply. */
export function buildChatSSEBodyWithTool(options: {
  toolName?: string;
  toolResult?: string;
  replyChunks?: string[];
  conversationId?: string;
}): string {
  const toolName = options.toolName ?? 'get_brand_info';
  const toolResult = options.toolResult ?? '{"brand": "Visionarias"}';
  const chunks = options.replyChunks ?? ['Basado en tu marca: Visionarias.'];
  const conversationId = options.conversationId ?? 'conv-mock-tool-001';

  return [
    sseEvent('status', { state: 'thinking' }),
    sseEvent('tool_start', { tool: toolName, args: {} }),
    sseEvent('tool_result', { tool: toolName, result: toolResult }),
    sseEvent('status', { state: 'responding' }),
    ...chunks.map((c) => sseEvent('text_chunk', { content: c })),
    sseEvent('done', { conversation_id: conversationId }),
  ].join('');
}

/** Stream that terminates with an error event. */
export function buildChatSSEBodyWithError(message = 'Error interno del copilot'): string {
  return [
    sseEvent('status', { state: 'thinking' }),
    sseEvent('error', { message }),
  ].join('');
}

// ── Route mock setup ─────────────────────────────────────────────────────────

export interface ChatMockOptions {
  /** Text chunks to include in the SSE reply. Defaults to CHAT_MOCK_SIMPLE. */
  textChunks?: string[];
  /** Conversation ID included in the "done" event. */
  conversationId?: string;
  /**
   * If set, the mock returns an HTTP error instead of a streaming SSE body.
   * Useful to test error handling in useCopilotChat.
   */
  httpError?: { status: number; body: string };
  /**
   * If set, the mock appends tool_start + tool_result events before the text reply.
   */
  withTool?: { name: string; result: string };
}

/**
 * Intercept POST /api/v1/copilot/chat and return a deterministic SSE stream.
 *
 * Playwright fulfills the request immediately with a complete body — there is
 * no real streaming, but the SSE parser in `streamCopilotChat` reads the same
 * chunked format and will process all events correctly.
 */
export async function setupCopilotChatMock(
  page: Page,
  options: ChatMockOptions = {},
) {
  await page.route('**/api/v1/copilot/chat', async (route) => {
    if (options.httpError) {
      await route.fulfill({
        status: options.httpError.status,
        body: options.httpError.body,
        contentType: 'text/plain',
      });
      return;
    }

    let body: string;
    if (options.withTool) {
      body = buildChatSSEBodyWithTool({
        toolName: options.withTool.name,
        toolResult: options.withTool.result,
        replyChunks: options.textChunks ?? CHAT_MOCK_SIMPLE.textChunks,
        conversationId: options.conversationId ?? CHAT_MOCK_SIMPLE.conversationId,
      });
    } else {
      body = buildChatSSEBody({
        textChunks: options.textChunks ?? CHAT_MOCK_SIMPLE.textChunks,
        conversationId: options.conversationId ?? CHAT_MOCK_SIMPLE.conversationId,
      });
    }

    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body,
    });
  });
}

/**
 * Mock the copilot events endpoint (fire-and-forget, should always return 204).
 * Register this to avoid unexpected real network calls during tests.
 */
export async function mockCopilotEvents(page: Page) {
  await page.route('**/api/v1/copilot/events/record', async (route) => {
    await route.fulfill({ status: 204 });
  });
}

/**
 * Full copilot chat mock setup: intercepts both chat stream and event recording.
 * Use this as a one-call setup in smoke/regression tests for copilot.
 */
export async function setupCopilotChatMocks(
  page: Page,
  chatOptions: ChatMockOptions = {},
) {
  await setupCopilotChatMock(page, chatOptions);
  await mockCopilotEvents(page);
}
