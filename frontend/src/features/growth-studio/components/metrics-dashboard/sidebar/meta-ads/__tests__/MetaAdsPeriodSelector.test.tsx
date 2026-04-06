import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MetaAdsPeriodSelector } from '../MetaAdsPeriodSelector';

describe('MetaAdsPeriodSelector', () => {
  it('renders all three period options', () => {
    render(<MetaAdsPeriodSelector value="30d" onChange={() => {}} />);
    // Component uses "dias" without accent
    expect(screen.getByText('7 dias')).toBeInTheDocument();
    expect(screen.getByText('30 dias')).toBeInTheDocument();
    expect(screen.getByText('90 dias')).toBeInTheDocument();
  });

  it('calls onChange when a period button is clicked', () => {
    const onChange = vi.fn();
    render(<MetaAdsPeriodSelector value="30d" onChange={onChange} />);
    fireEvent.click(screen.getByText('7 dias'));
    expect(onChange).toHaveBeenCalledWith('7d');
  });

  it('calls onChange with 90d when that button is clicked', () => {
    const onChange = vi.fn();
    render(<MetaAdsPeriodSelector value="7d" onChange={onChange} />);
    fireEvent.click(screen.getByText('90 dias'));
    expect(onChange).toHaveBeenCalledWith('90d');
  });

  it('highlights the active period with bg-background class', () => {
    const { container } = render(
      <MetaAdsPeriodSelector value="90d" onChange={() => {}} />,
    );
    const buttons = container.querySelectorAll('button');
    const activeButton = Array.from(buttons).find(b => b.textContent === '90 dias');
    expect(activeButton?.className).toContain('bg-background');
  });

  it('does not highlight inactive periods with bg-background class', () => {
    const { container } = render(
      <MetaAdsPeriodSelector value="30d" onChange={() => {}} />,
    );
    const buttons = container.querySelectorAll('button');
    const inactiveButton = Array.from(buttons).find(b => b.textContent === '7 dias');
    expect(inactiveButton?.className).not.toContain('bg-background');
  });

  it('renders buttons with type="button" to prevent form submission', () => {
    const { container } = render(
      <MetaAdsPeriodSelector value="30d" onChange={() => {}} />,
    );
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
      expect(button.getAttribute('type')).toBe('button');
    });
  });
});
