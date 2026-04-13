import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Copilot sidebar.
 *
 * Locator strategy:
 * - Role-based selectors preferred (getByRole, getByLabel, getByText)
 * - data-testid only where semantic selectors are ambiguous
 * - Never CSS selectors
 */
export class CopilotPage {
  // Sidebar container (data-testid set in copilot-sidebar.tsx aside element)
  readonly sidebar: Locator;

  // Chat input area
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly stopButton: Locator;

  // Message list container (scroll area inside CopilotChat)
  readonly messageList: Locator;

  // Focus bar (only visible when focusEntity is set)
  readonly focusBar: Locator;
  readonly focusBarLabel: Locator;
  readonly focusBarExitButton: Locator;
  readonly focusBarUndoButton: Locator;
  readonly focusBarProgressDots: Locator;

  // Header controls
  readonly headerTitle: Locator;
  readonly clearConversationButton: Locator;
  readonly closeSidebarButton: Locator;
  readonly expandButton: Locator;

  // Interview cards (rendered inside AssistantMessage)
  readonly checkpointCard: Locator;
  readonly checkpointConfirmButton: Locator;
  readonly checkpointReviseButton: Locator;

  readonly clarifyCard: Locator;

  readonly alternativesCard: Locator;

  readonly interviewCompleteCard: Locator;

  // Typing indicator
  readonly typingIndicator: Locator;

  // Suggested actions strip
  readonly suggestedActions: Locator;

  // Preview pane (only visible in "expanded" state)
  readonly previewPane: Locator;

  constructor(public readonly page: Page) {
    // Sidebar
    this.sidebar = page.getByTestId('copilot-sidebar');

    // Chat input — aria-label="Mensaje" set on textarea in copilot-input.tsx
    this.chatInput = page.getByLabel('Mensaje').first();
    this.sendButton = page.getByRole('button', { name: /enviar/i }).first();
    this.stopButton = page.getByRole('button', { name: /detener/i }).first();

    // Message area — the scrollable div wrapping virtual list
    this.messageList = page.locator('[data-testid="copilot-messages"]');

    // Focus bar
    this.focusBar = page.locator('[data-testid="focus-bar"]');
    this.focusBarLabel = page.locator('[data-testid="focus-bar"] span').first();
    this.focusBarExitButton = page.getByRole('button', { name: /salir de focus/i }).first();
    this.focusBarUndoButton = page.getByRole('button', { name: /deshacer todo/i }).first();
    this.focusBarProgressDots = page.getByTestId('progress-dot');

    // Header
    this.headerTitle = page.locator('[data-testid="copilot-header"] span').first();
    this.clearConversationButton = page.getByRole('button', { name: /nueva conversación/i }).first();
    this.closeSidebarButton = page.getByRole('button', { name: /cerrar/i }).first();
    this.expandButton = page.getByRole('button', { name: /expandir/i }).first();

    // Interview cards — keyed by aria-label on primary action buttons
    this.checkpointCard = page.locator('[data-testid="checkpoint-card"]');
    this.checkpointConfirmButton = page.getByRole('button', { name: /perfecto, sigamos/i }).first();
    this.checkpointReviseButton = page.getByRole('button', { name: /ajustar algo/i }).first();

    this.clarifyCard = page.locator('[data-testid="clarify-card"]');

    this.alternativesCard = page.locator('[data-testid="alternatives-card"]');

    this.interviewCompleteCard = page.locator('[data-testid="interview-complete-card"]');

    // Typing indicator
    this.typingIndicator = page.locator('[data-testid="typing-indicator"]');

    // Suggested actions
    this.suggestedActions = page.locator('[data-testid="suggested-actions"]');

    // Preview pane
    this.previewPane = page.locator('[data-testid="copilot-preview-pane"]');
  }

  // ── Navigation helpers ──────────────────────────────────────────────────

  /** Navigate to a tenant route that renders the copilot sidebar. */
  async goto(tenantId: string, path = '') {
    await this.page.goto(`/${tenantId}${path ? `/${path}` : ''}`, {
      waitUntil: 'domcontentloaded',
    });
  }

  // ── State assertions ─────────────────────────────────────────────────────

  /** Wait for the sidebar to be in an "open" or "expanded" visible state. */
  async expectSidebarOpen() {
    await expect(this.chatInput).toBeVisible({ timeout: 15_000 });
  }

  /** The chat input is editable and send button present. */
  async expectInputReady() {
    await expect(this.chatInput).toBeEnabled({ timeout: 10_000 });
    await expect(this.sendButton).toBeVisible();
  }

  /** Focus bar is visible with a given label text. */
  async expectFocusMode(label: string) {
    await expect(this.focusBar).toBeVisible({ timeout: 10_000 });
    await expect(this.page.getByText(label).first()).toBeVisible();
  }

  /** Focus bar is not rendered (no active focus entity). */
  async expectNoFocusMode() {
    await expect(this.focusBar).not.toBeVisible();
  }

  /** Assert that a user message with the given text exists. */
  async expectUserMessage(text: string) {
    await expect(this.page.getByText(text).first()).toBeVisible({ timeout: 10_000 });
  }

  /** Assert that an assistant message containing the given text exists. */
  async expectAssistantMessage(text: string) {
    await expect(this.page.getByText(text).first()).toBeVisible({ timeout: 15_000 });
  }

  /** Typing indicator is visible (streaming in progress). */
  async expectStreaming() {
    await expect(this.typingIndicator).toBeVisible({ timeout: 10_000 });
  }

  // ── Interaction helpers ──────────────────────────────────────────────────

  /** Type and send a chat message. */
  async sendMessage(text: string) {
    await this.chatInput.click();
    await this.chatInput.fill(text);
    await this.sendButton.click();
  }

  /** Type a message and submit with Enter. */
  async sendMessageWithEnter(text: string) {
    await this.chatInput.click();
    await this.chatInput.fill(text);
    await this.chatInput.press('Enter');
  }

  /** Click the "Salir de Focus" button and confirm if a dialog appears. */
  async exitFocusMode({ confirm = false } = {}) {
    await this.focusBarExitButton.click();
    if (confirm) {
      await this.page.getByRole('button', { name: /salir sin guardar/i }).click();
    }
  }

  /** Click the checkpoint card confirm button. */
  async confirmCheckpoint() {
    await this.checkpointConfirmButton.click();
  }

  /** Click the checkpoint card revise button. */
  async reviseCheckpoint() {
    await this.checkpointReviseButton.click();
  }
}
