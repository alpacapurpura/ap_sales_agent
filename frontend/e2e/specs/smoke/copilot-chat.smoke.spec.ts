import { type Page } from '@playwright/test';
import { test, expect } from '../../fixtures/auth.fixture';
import { CopilotPage } from '../../pages/copilot.pom';
import {
  setupCopilotChatMocks,
  CHAT_MOCK_SIMPLE,
} from '../../fixtures/copilot-chat.fixture';

/**
 * Smoke tests for the Copilot chat flow.
 *
 * These tests verify that:
 * - A user message appears in the list after sending
 * - The mocked SSE stream response is rendered
 *
 * All API calls are mocked — no real LLM or backend is required.
 */
test.describe('Copilot Chat @smoke', () => {
  /**
   * Helper: navigate to a page with the copilot sidebar and open the panel.
   * Returns the CopilotPage POM ready for interaction.
   */
  async function openCopilot(page: Page, tenantId: string) {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    // Open the panel by clicking the rail button
    await page.locator('[data-testid="copilot-sidebar"] button').first().click();
    await copilot.expectSidebarOpen();
    return copilot;
  }

  test.beforeEach(async ({ page }) => {
    // Mock nudges to empty (no nudge banners that could interfere)
    await page.route('**/api/v1/copilot/nudge-context**', async (route) => {
      await route.fulfill({ json: { nudges: [] }, status: 200 });
    });

    // Mock copilot chat + events endpoints
    await setupCopilotChatMocks(page, {
      textChunks: CHAT_MOCK_SIMPLE.textChunks,
      conversationId: CHAT_MOCK_SIMPLE.conversationId,
    });
  });

  test('user message appears in chat list after sending', async ({ page, tenantId }) => {
    const copilot = await openCopilot(page, tenantId);

    const userMessage = '¿Cuál es mi propuesta de valor?';
    await copilot.sendMessage(userMessage);

    // User message must appear in the virtual list
    await copilot.expectUserMessage(userMessage);
  });

  test('assistant response renders after mock SSE stream completes', async ({ page, tenantId }) => {
    const copilot = await openCopilot(page, tenantId);

    await copilot.sendMessage('Hola Copilot');

    // The mocked stream emits the CHAT_MOCK_SIMPLE text chunks — wait for them
    const expectedText = CHAT_MOCK_SIMPLE.textChunks[0];
    await copilot.expectAssistantMessage(expectedText);
  });

  test('input is cleared after sending a message', async ({ page, tenantId }) => {
    const copilot = await openCopilot(page, tenantId);

    await copilot.chatInput.fill('Prueba de envío');
    await copilot.sendButton.click();

    // After send, input should be empty
    await expect(copilot.chatInput).toHaveValue('', { timeout: 5_000 });
  });

  test('send button is disabled when input is empty', async ({ page, tenantId }) => {
    const copilot = await openCopilot(page, tenantId);

    // With no text typed, the send button should be disabled
    await expect(copilot.sendButton).toBeDisabled();
  });

  test('message can be sent with Enter key', async ({ page, tenantId }) => {
    const copilot = await openCopilot(page, tenantId);

    const msg = '¿Qué me falta en mi marca?';
    await copilot.sendMessageWithEnter(msg);

    // The user message must appear
    await copilot.expectUserMessage(msg);
  });
});
