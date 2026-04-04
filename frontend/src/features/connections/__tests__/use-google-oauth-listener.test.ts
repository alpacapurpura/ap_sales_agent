import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useGoogleOAuthListener } from '@/features/connections/hooks/use-google-oauth-listener';
import { OAUTH_MESSAGE_TYPES } from '@/features/connections/lib/oauth-constants';

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('useGoogleOAuthListener', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('registers a message event listener on mount', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    const onSuccess = vi.fn();

    renderHook(() => useGoogleOAuthListener({ onSuccess }));

    expect(addSpy).toHaveBeenCalledWith('message', expect.any(Function));
  });

  it('removes the message event listener on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const onSuccess = vi.fn();

    const { unmount } = renderHook(() => useGoogleOAuthListener({ onSuccess }));
    unmount();

    expect(removeSpy).toHaveBeenCalledWith('message', expect.any(Function));
  });

  it('calls onSuccess with code when GOOGLE_SUCCESS message is received from same origin', async () => {
    const onSuccess = vi.fn();
    renderHook(() => useGoogleOAuthListener({ onSuccess }));

    const event = new MessageEvent('message', {
      data: { type: OAUTH_MESSAGE_TYPES.GOOGLE_SUCCESS, code: 'auth-code-123' },
      origin: window.location.origin,
    });
    window.dispatchEvent(event);

    // Allow async handler to complete
    await vi.waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith('auth-code-123');
    });
  });

  it('ignores messages from different origins (origin validation)', () => {
    const onSuccess = vi.fn();
    const onError = vi.fn();
    renderHook(() => useGoogleOAuthListener({ onSuccess, onError }));

    const event = new MessageEvent('message', {
      data: { type: OAUTH_MESSAGE_TYPES.GOOGLE_SUCCESS, code: 'stolen-code' },
      origin: 'https://evil.example.com',
    });
    window.dispatchEvent(event);

    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it('calls onError when GOOGLE_ERROR message is received from same origin', () => {
    const onSuccess = vi.fn();
    const onError = vi.fn();
    renderHook(() => useGoogleOAuthListener({ onSuccess, onError }));

    const event = new MessageEvent('message', {
      data: { type: OAUTH_MESSAGE_TYPES.GOOGLE_ERROR, error: 'access_denied' },
      origin: window.location.origin,
    });
    window.dispatchEvent(event);

    expect(onError).toHaveBeenCalledWith('access_denied');
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('does not register listener when enabled is false', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    const onSuccess = vi.fn();

    renderHook(() => useGoogleOAuthListener({ onSuccess, enabled: false }));

    const messageListeners = addSpy.mock.calls.filter(([event]) => event === 'message');
    expect(messageListeners).toHaveLength(0);
  });

  it('falls back to "Unknown error" when error field is missing in GOOGLE_ERROR message', () => {
    const onSuccess = vi.fn();
    const onError = vi.fn();
    renderHook(() => useGoogleOAuthListener({ onSuccess, onError }));

    const event = new MessageEvent('message', {
      data: { type: OAUTH_MESSAGE_TYPES.GOOGLE_ERROR },
      origin: window.location.origin,
    });
    window.dispatchEvent(event);

    expect(onError).toHaveBeenCalledWith('Unknown error');
  });
});
