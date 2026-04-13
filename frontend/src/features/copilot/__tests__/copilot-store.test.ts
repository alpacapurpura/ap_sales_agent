import { describe, it, expect, beforeEach } from 'vitest';
import { useCopilotStore, MAX_MESSAGES } from '@/features/copilot/store/copilot-store';
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
      sidebarState: 'collapsed',
      conversationId: null,
      messages: [],
      status: 'idle',
      currentRoute: null,
      pendingUIActions: [],
      activeProcedure: null,
      selectedFields: [],
      focusEntity: null,
      focusSnapshot: null,
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
    });
  });

  // ── Panel toggle ───────────────────────────────────────────────────────────

  it('togglePanel flips isOpen from false to true', () => {
    const { togglePanel } = useCopilotStore.getState();
    togglePanel();
    expect(useCopilotStore.getState().isOpen).toBe(true);
  });

  it('togglePanel flips isOpen from true to false', () => {
    useCopilotStore.setState({ sidebarState: 'open' });
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
    useCopilotStore.setState({ sidebarState: 'open' });
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

  // ── Message limit (MAX_MESSAGES) ───────────────────────────────────────────

  it('MAX_MESSAGES is exported and equals 100', () => {
    expect(MAX_MESSAGES).toBe(100);
  });

  it('addMessage does not trim when count is at the limit', () => {
    const msgs = Array.from({ length: MAX_MESSAGES }, (_, i) =>
      makeMessage({ id: `msg-${i}`, content: `Message ${i}` })
    );
    msgs.forEach((m) => useCopilotStore.getState().addMessage(m));
    expect(useCopilotStore.getState().messages).toHaveLength(MAX_MESSAGES);
  });

  it('addMessage trims oldest messages when limit is exceeded', () => {
    // Fill to MAX_MESSAGES, then add one more
    const msgs = Array.from({ length: MAX_MESSAGES }, (_, i) =>
      makeMessage({ id: `msg-${i}`, content: `Message ${i}` })
    );
    msgs.forEach((m) => useCopilotStore.getState().addMessage(m));

    const overflow = makeMessage({ id: 'msg-overflow', content: 'Overflow' });
    useCopilotStore.getState().addMessage(overflow);

    const { messages } = useCopilotStore.getState();
    expect(messages).toHaveLength(MAX_MESSAGES);
    // Oldest message (index 0) should be trimmed
    expect(messages[0].id).toBe('msg-1');
    // The overflow message should be the last one
    expect(messages[messages.length - 1].id).toBe('msg-overflow');
  });

  it('addMessage keeps only the last MAX_MESSAGES when many are added', () => {
    const total = MAX_MESSAGES + 50;
    for (let i = 0; i < total; i++) {
      useCopilotStore.getState().addMessage(
        makeMessage({ id: `msg-${i}`, content: `Message ${i}` })
      );
    }
    const { messages } = useCopilotStore.getState();
    expect(messages).toHaveLength(MAX_MESSAGES);
    // The first retained message should be msg-50 (total - MAX_MESSAGES)
    expect(messages[0].id).toBe('msg-50');
    expect(messages[messages.length - 1].id).toBe(`msg-${total - 1}`);
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

describe('Focus and Interview state', () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: 'collapsed',
      focusEntity: null,
      focusSnapshot: null,
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
    });
  });

  it('should default to no focus entity', () => {
    const state = useCopilotStore.getState();
    expect(state.focusEntity).toBeNull();
    expect(state.focusSnapshot).toBeNull();
  });

  it('should set and clear focus entity', () => {
    const { setFocusEntity, clearFocus } = useCopilotStore.getState();
    setFocusEntity({ domain: 'offer', entityId: '123', label: 'Mi Oferta' });

    expect(useCopilotStore.getState().focusEntity).toEqual({
      domain: 'offer',
      entityId: '123',
      label: 'Mi Oferta',
    });

    clearFocus();
    expect(useCopilotStore.getState().focusEntity).toBeNull();
    expect(useCopilotStore.getState().focusSnapshot).toBeNull();
  });

  it('should set and clear interview session', () => {
    const { setInterviewSession, clearInterview } = useCopilotStore.getState();
    setInterviewSession('session-abc');

    expect(useCopilotStore.getState().interviewSessionId).toBe('session-abc');

    clearInterview();
    expect(useCopilotStore.getState().interviewSessionId).toBeNull();
    expect(useCopilotStore.getState().interviewProgress).toBeNull();
  });

  it('should update and clear preview data', () => {
    const { updatePreviewData, clearPreviewData } = useCopilotStore.getState();
    updatePreviewData({ 'strategy.name': 'Test' });
    updatePreviewData({ 'pricing.amount': 100 });

    const state = useCopilotStore.getState();
    expect(state.previewData).toEqual({
      'strategy.name': 'Test',
      'pricing.amount': 100,
    });

    clearPreviewData();
    expect(useCopilotStore.getState().previewData).toBeNull();
  });
});

describe('sidebarState', () => {
  beforeEach(() => {
    useCopilotStore.setState({ sidebarState: 'collapsed' });
  });

  it('should default to collapsed', () => {
    expect(useCopilotStore.getState().sidebarState).toBe('collapsed');
  });

  it('should transition between states', () => {
    const { setSidebarState } = useCopilotStore.getState();
    setSidebarState('open');
    expect(useCopilotStore.getState().sidebarState).toBe('open');

    setSidebarState('expanded');
    expect(useCopilotStore.getState().sidebarState).toBe('expanded');

    setSidebarState('collapsed');
    expect(useCopilotStore.getState().sidebarState).toBe('collapsed');
  });
});

describe('Interview UIAction types', () => {
  beforeEach(() => {
    useCopilotStore.setState({
      messages: [],
      status: 'idle',
    });
  });

  it('should support alternatives_card UIAction type', () => {
    const msg: CopilotMessage = {
      id: 'msg-1',
      role: 'assistant',
      content: 'Here are some options:',
      timestamp: Date.now(),
      uiActions: [{
        type: 'alternatives_card',
        field_path: 'strategy.target_audience',
        question: 'Who is your target audience?',
        alternatives: [
          { id: '1', title: 'Option A', description: 'First option', recommended: true },
          { id: '2', title: 'Option B', description: 'Second option' },
        ],
        allow_custom: true,
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    const stored = useCopilotStore.getState().messages[0];
    expect(stored.uiActions![0].type).toBe('alternatives_card');
    expect(stored.uiActions![0].alternatives).toHaveLength(2);
  });

  it('should support checkpoint_card UIAction type', () => {
    const msg: CopilotMessage = {
      id: 'msg-2',
      role: 'assistant',
      content: 'Block complete!',
      timestamp: Date.now(),
      uiActions: [{
        type: 'checkpoint_card',
        block_id: 'strategy',
        block_label: 'Estrategia',
        summary: { name: 'Test' },
        health_score: 85,
        blocks_progress: { completed: 1, total: 5 },
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    const action = useCopilotStore.getState().messages[0].uiActions![0];
    expect(action.type).toBe('checkpoint_card');
    expect(action.health_score).toBe(85);
  });

  it('should update UIAction status via updateUIActionStatus', () => {
    const msg: CopilotMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Options:',
      timestamp: Date.now(),
      uiActions: [{
        type: 'alternatives_card',
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    useCopilotStore.getState().updateUIActionStatus('msg-3', 0, 'resolved');
    const action = useCopilotStore.getState().messages[0].uiActions![0];
    expect(action.card_status).toBe('resolved');
  });

  it('updateUIActionStatus is no-op for non-existent message', () => {
    useCopilotStore.getState().updateUIActionStatus('non-existent', 0, 'resolved');
    expect(useCopilotStore.getState().messages).toHaveLength(0);
  });
});

describe('backward compatibility', () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: 'collapsed',
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
    });
  });

  it('isOpen should reflect sidebarState', () => {
    const { setSidebarState } = useCopilotStore.getState();
    setSidebarState('collapsed');
    expect(useCopilotStore.getState().isOpen).toBe(false);

    setSidebarState('open');
    expect(useCopilotStore.getState().isOpen).toBe(true);

    setSidebarState('expanded');
    expect(useCopilotStore.getState().isOpen).toBe(true);
  });

  it('togglePanel should work with sidebarState', () => {
    const { togglePanel, setSidebarState } = useCopilotStore.getState();
    setSidebarState('collapsed');
    togglePanel();
    expect(useCopilotStore.getState().sidebarState).toBe('open');

    togglePanel();
    expect(useCopilotStore.getState().sidebarState).toBe('collapsed');
  });

  it('openPanel should set sidebarState to open', () => {
    useCopilotStore.getState().openPanel();
    expect(useCopilotStore.getState().sidebarState).toBe('open');
  });

  it('closePanel should set sidebarState to collapsed', () => {
    useCopilotStore.getState().setSidebarState('open');
    useCopilotStore.getState().closePanel();
    expect(useCopilotStore.getState().sidebarState).toBe('collapsed');
  });

});
