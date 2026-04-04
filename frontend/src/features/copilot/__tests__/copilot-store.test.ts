import { describe, it, expect, beforeEach } from 'vitest';
import { useCopilotStore } from '@/features/copilot/store/copilot-store';
import type { CopilotMessage, UIAction, ActiveProcedure } from '@/features/copilot/store/copilot-store';

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeMessage(overrides: Partial<CopilotMessage> = {}): CopilotMessage {
  return {
    id: 'msg-1',
    role: 'user',
    content: 'Hello',
    timestamp: Date.now(),
    ...overrides,
  };
}

function makeUIAction(overrides: Partial<UIAction> = {}): UIAction {
  return {
    type: 'navigate',
    route: '/dashboard',
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('copilot-store', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useCopilotStore.setState({
      isOpen: false,
      conversationId: null,
      messages: [],
      status: 'idle',
      currentRoute: null,
      pendingUIActions: [],
      activeProcedure: null,
      selectedFields: [],
    });
  });

  // ── Panel toggle ───────────────────────────────────────────────────────────

  it('togglePanel flips isOpen from false to true', () => {
    const { togglePanel } = useCopilotStore.getState();
    togglePanel();
    expect(useCopilotStore.getState().isOpen).toBe(true);
  });

  it('togglePanel flips isOpen from true to false', () => {
    useCopilotStore.setState({ isOpen: true });
    const { togglePanel } = useCopilotStore.getState();
    togglePanel();
    expect(useCopilotStore.getState().isOpen).toBe(false);
  });

  it('openPanel sets isOpen to true', () => {
    const { openPanel } = useCopilotStore.getState();
    openPanel();
    expect(useCopilotStore.getState().isOpen).toBe(true);
  });

  it('closePanel sets isOpen to false', () => {
    useCopilotStore.setState({ isOpen: true });
    const { closePanel } = useCopilotStore.getState();
    closePanel();
    expect(useCopilotStore.getState().isOpen).toBe(false);
  });

  // ── addMessage ─────────────────────────────────────────────────────────────

  it('addMessage appends message to conversation', () => {
    const msg = makeMessage({ id: 'msg-a', content: 'Test message' });
    useCopilotStore.getState().addMessage(msg);
    expect(useCopilotStore.getState().messages).toHaveLength(1);
    expect(useCopilotStore.getState().messages[0]).toEqual(msg);
  });

  it('addMessage accumulates multiple messages in order', () => {
    const msg1 = makeMessage({ id: 'msg-1', content: 'First' });
    const msg2 = makeMessage({ id: 'msg-2', role: 'assistant', content: 'Second' });
    useCopilotStore.getState().addMessage(msg1);
    useCopilotStore.getState().addMessage(msg2);
    const { messages } = useCopilotStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[0].content).toBe('First');
    expect(messages[1].content).toBe('Second');
  });

  // ── enqueuUIAction / dequeuUIAction ────────────────────────────────────────

  it('enqueuUIAction adds action to pending queue', () => {
    const action = makeUIAction({ type: 'navigate', route: '/brand' });
    useCopilotStore.getState().enqueuUIAction(action);
    expect(useCopilotStore.getState().pendingUIActions).toHaveLength(1);
    expect(useCopilotStore.getState().pendingUIActions[0]).toEqual(action);
  });

  it('dequeuUIAction removes and returns first action (FIFO)', () => {
    const action1 = makeUIAction({ type: 'navigate', route: '/brand' });
    const action2 = makeUIAction({ type: 'scroll_to_field', field_id: 'uvp' });
    useCopilotStore.getState().enqueuUIAction(action1);
    useCopilotStore.getState().enqueuUIAction(action2);

    const dequeued = useCopilotStore.getState().dequeuUIAction();
    expect(dequeued).toEqual(action1);
    expect(useCopilotStore.getState().pendingUIActions).toHaveLength(1);
    expect(useCopilotStore.getState().pendingUIActions[0]).toEqual(action2);
  });

  it('dequeuUIAction returns undefined when queue is empty', () => {
    const result = useCopilotStore.getState().dequeuUIAction();
    expect(result).toBeUndefined();
  });

  // ── appendToLastAssistant ──────────────────────────────────────────────────

  it('appendToLastAssistant concatenates chunk to last assistant message', () => {
    const assistantMsg = makeMessage({ id: 'a1', role: 'assistant', content: 'Hello' });
    useCopilotStore.getState().addMessage(assistantMsg);
    useCopilotStore.getState().appendToLastAssistant(' world');
    expect(useCopilotStore.getState().messages[0].content).toBe('Hello world');
  });

  it('appendToLastAssistant is a no-op when last message is from user', () => {
    const userMsg = makeMessage({ id: 'u1', role: 'user', content: 'Question?' });
    useCopilotStore.getState().addMessage(userMsg);
    useCopilotStore.getState().appendToLastAssistant(' ignored');
    expect(useCopilotStore.getState().messages[0].content).toBe('Question?');
  });

  // ── clearMessages ──────────────────────────────────────────────────────────

  it('clearMessages resets messages, conversationId, and status', () => {
    useCopilotStore.setState({
      messages: [makeMessage()],
      conversationId: 'conv-123',
      status: 'streaming',
    });
    useCopilotStore.getState().clearMessages();
    const state = useCopilotStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.conversationId).toBeNull();
    expect(state.status).toBe('idle');
  });

  // ── selectedFields ─────────────────────────────────────────────────────────

  it('addSelectedField adds a field and prevents duplicates', () => {
    const field = { fieldId: 'uvp', fieldLabel: 'UVP', fieldValue: 'My value' };
    useCopilotStore.getState().addSelectedField(field);
    useCopilotStore.getState().addSelectedField(field); // duplicate
    expect(useCopilotStore.getState().selectedFields).toHaveLength(1);
  });

  it('removeSelectedField removes field by id', () => {
    useCopilotStore.setState({
      selectedFields: [
        { fieldId: 'uvp', fieldLabel: 'UVP', fieldValue: 'v1' },
        { fieldId: 'name', fieldLabel: 'Name', fieldValue: 'v2' },
      ],
    });
    useCopilotStore.getState().removeSelectedField('uvp');
    expect(useCopilotStore.getState().selectedFields).toHaveLength(1);
    expect(useCopilotStore.getState().selectedFields[0].fieldId).toBe('name');
  });

  // ── activeProcedure ────────────────────────────────────────────────────────

  it('setActiveProcedure stores the procedure and clearActiveProcedure resets it', () => {
    const proc: ActiveProcedure = {
      id: 'proc-1',
      name: 'Setup Brand',
      steps: [{ id: 's1', label: 'Step 1', status: 'current' }],
      currentStepIndex: 0,
    };
    useCopilotStore.getState().setActiveProcedure(proc);
    expect(useCopilotStore.getState().activeProcedure).toEqual(proc);

    useCopilotStore.getState().clearActiveProcedure();
    expect(useCopilotStore.getState().activeProcedure).toBeNull();
  });
});
