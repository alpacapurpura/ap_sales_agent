import { describe, it, expect, vi, beforeEach } from 'vitest';
import { openOAuthPopup } from '@/features/connections/utils/open-oauth-popup';

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('openOAuthPopup', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock screen dimensions
    Object.defineProperty(window, 'screen', {
      value: { width: 1920, height: 1080 },
      writable: true,
      configurable: true,
    });

    // Mock window.open
    vi.spyOn(window, 'open').mockReturnValue(null);
  });

  it('calls window.open with the provided URL', () => {
    openOAuthPopup({ url: 'https://accounts.google.com/oauth' });
    expect(window.open).toHaveBeenCalledWith(
      'https://accounts.google.com/oauth',
      expect.any(String),
      expect.any(String)
    );
  });

  it('uses default popup name "oauth-popup" when none is provided', () => {
    openOAuthPopup({ url: 'https://accounts.google.com/oauth' });
    expect(window.open).toHaveBeenCalledWith(
      expect.any(String),
      'oauth-popup',
      expect.any(String)
    );
  });

  it('uses provided popup name when specified', () => {
    openOAuthPopup({ url: 'https://example.com', name: 'google-auth' });
    expect(window.open).toHaveBeenCalledWith(
      expect.any(String),
      'google-auth',
      expect.any(String)
    );
  });

  it('centers the popup horizontally and vertically relative to screen', () => {
    // screen: 1920x1080, popup defaults: 520x640
    // left = 1920/2 - 520/2 = 960 - 260 = 700
    // top  = 1080/2 - 640/2 = 540 - 320 = 220
    openOAuthPopup({ url: 'https://example.com' });
    const featuresString = (window.open as ReturnType<typeof vi.fn>).mock.calls[0][2] as string;
    expect(featuresString).toContain('left=700');
    expect(featuresString).toContain('top=220');
  });

  it('respects custom width and height for centering math', () => {
    // screen: 1920x1080, custom: 400x500
    // left = 1920/2 - 400/2 = 960 - 200 = 760
    // top  = 1080/2 - 500/2 = 540 - 250 = 290
    openOAuthPopup({ url: 'https://example.com', width: 400, height: 500 });
    const featuresString = (window.open as ReturnType<typeof vi.fn>).mock.calls[0][2] as string;
    expect(featuresString).toContain('width=400');
    expect(featuresString).toContain('height=500');
    expect(featuresString).toContain('left=760');
    expect(featuresString).toContain('top=290');
  });

  it('includes toolbar=no and menubar=no in features string', () => {
    openOAuthPopup({ url: 'https://example.com' });
    const featuresString = (window.open as ReturnType<typeof vi.fn>).mock.calls[0][2] as string;
    expect(featuresString).toContain('toolbar=no');
    expect(featuresString).toContain('menubar=no');
  });

  it('returns the Window object from window.open', () => {
    const fakeWindow = {} as Window;
    vi.spyOn(window, 'open').mockReturnValue(fakeWindow);
    const result = openOAuthPopup({ url: 'https://example.com' });
    expect(result).toBe(fakeWindow);
  });
});
