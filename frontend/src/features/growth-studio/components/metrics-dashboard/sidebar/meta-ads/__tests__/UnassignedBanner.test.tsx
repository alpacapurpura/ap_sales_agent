import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { UnassignedBanner } from '../UnassignedBanner';

describe('UnassignedBanner', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the count and an assign button', () => {
    render(<UnassignedBanner count={3} onAssignClick={vi.fn()} />);
    expect(screen.getByText(/3/)).toBeInTheDocument();
    expect(screen.getByText(/sin asignar/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Asignar/i })).toBeInTheDocument();
  });

  it('pluralizes correctly', () => {
    const { rerender } = render(<UnassignedBanner count={1} onAssignClick={vi.fn()} />);
    expect(screen.getByText(/1 campaña sin asignar/i)).toBeInTheDocument();
    rerender(<UnassignedBanner count={5} onAssignClick={vi.fn()} />);
    expect(screen.getByText(/5 campañas sin asignar/i)).toBeInTheDocument();
  });

  it('calls onAssignClick when the assign button is clicked', () => {
    const onAssign = vi.fn();
    render(<UnassignedBanner count={2} onAssignClick={onAssign} />);
    fireEvent.click(screen.getByRole('button', { name: /Asignar/i }));
    expect(onAssign).toHaveBeenCalled();
  });

  it('hides itself after dismiss click and persists to localStorage', () => {
    const { container } = render(<UnassignedBanner count={2} onAssignClick={vi.fn()} />);
    const dismiss = screen.getByRole('button', { name: /cerrar/i });
    fireEvent.click(dismiss);
    expect(container.firstChild).toBeNull();
    // localStorage key was set
    const keys = Object.keys(localStorage);
    expect(keys.some(k => k.startsWith('meta-ads-unassigned-banner-dismissed'))).toBe(true);
  });

  it('does not render if already dismissed for today', () => {
    const today = new Date().toISOString().slice(0, 10);
    localStorage.setItem(`meta-ads-unassigned-banner-dismissed-${today}`, '1');
    const { container } = render(<UnassignedBanner count={2} onAssignClick={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when count is 0', () => {
    const { container } = render(<UnassignedBanner count={0} onAssignClick={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });
});
