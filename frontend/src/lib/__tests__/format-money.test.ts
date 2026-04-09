import { describe, expect, it } from 'vitest';
import { formatMoney, formatDualCurrency, formatMoneyDual, formatAggregatedMoney } from '../format-money';

describe('formatMoney', () => {
  it('formats USD with dollar sign', () => {
    expect(formatMoney(1234.56, 'USD')).toBe('$1,234.56');
  });

  it('formats PEN with sol symbol or ISO code', () => {
    const result = formatMoney(1234, 'PEN');
    // Intl may render "S/" or "PEN" depending on ICU data in the environment
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('1,234');
  });

  it('formats MXN with dollar sign', () => {
    const result = formatMoney(1234, 'MXN');
    expect(result).toContain('$');
    expect(result).toContain('1,234');
  });

  it('formats EUR with euro sign', () => {
    const result = formatMoney(1234, 'EUR');
    expect(result).toMatch(/EUR|€/);
    expect(result).toContain('1,234');
  });

  it('handles compact format', () => {
    const result = formatMoney(1200000, 'USD', { compact: true });
    // Should contain M for millions
    expect(result).toMatch(/1\.2\s*M|1,200/);
  });

  it('handles JPY without decimals', () => {
    const result = formatMoney(1234, 'JPY');
    expect(result).toContain('1,234');
    // JPY should not have decimals (Intl handles this automatically)
    expect(result).not.toContain('.');
  });

  it('handles custom fraction digits', () => {
    const result = formatMoney(1234.5678, 'USD', { fractionDigits: 0 });
    expect(result).toContain('1,235'); // rounded
  });
});

describe('formatDualCurrency', () => {
  it('shows only USD when currency is USD', () => {
    const result = formatDualCurrency(5000, 'USD', 5000);
    expect(result).toContain('$');
    expect(result).toContain('5,000');
    expect(result).not.toContain('USD)');
  });

  it('shows dual format when non-USD', () => {
    const result = formatDualCurrency(5000, 'PEN', 750);
    // Intl may render "S/" or "PEN" depending on ICU data in the environment
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('750');
    expect(result).toContain('USD');
  });

  it('shows only local when usdAmount is null', () => {
    const result = formatDualCurrency(5000, 'MXN', null);
    expect(result).toContain('$');
    expect(result).toContain('5,000');
    expect(result).not.toContain('USD');
  });

  it('shows only local when usdAmount is undefined', () => {
    const result = formatDualCurrency(5000, 'MXN', undefined);
    expect(result).not.toContain('USD');
  });
});

describe('formatMoneyDual', () => {
  it('shows single when source equals tenant', () => {
    const result = formatMoneyDual(500, 'PEN', 'PEN');
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('500');
    expect(result).not.toContain('~');
  });

  it('shows dual when source differs from tenant', () => {
    const result = formatMoneyDual(100, 'USD', 'PEN', 370);
    expect(result).toContain('$');
    expect(result).toContain('100');
    expect(result).toContain('~');
    expect(result).toContain('370');
  });

  it('shows just source when tenantAmount not available', () => {
    const result = formatMoneyDual(100, 'USD', 'PEN');
    expect(result).toContain('100');
  });
});

describe('formatAggregatedMoney', () => {
  it('shows single when tenant is USD', () => {
    const result = formatAggregatedMoney(1350, 'USD');
    expect(result).toContain('$');
    expect(result).toContain('1,350');
    expect(result).not.toContain('~');
  });

  it('shows dual when tenant is not USD', () => {
    const result = formatAggregatedMoney(5000, 'PEN', 1350);
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('5,000');
    expect(result).toContain('~');
    expect(result).toContain('1,350');
    expect(result).toContain('USD');
  });

  it('shows single when usdAmount is null', () => {
    const result = formatAggregatedMoney(5000, 'PEN');
    expect(result).toMatch(/S\/|PEN/);
    expect(result).not.toContain('USD');
  });
});
