import { describe, expect, it } from 'vitest';
import {
  formatTenantDate,
  formatTenantDateTime,
  formatTenantTime,
} from '../format-date';

describe('formatTenantDate', () => {
  it('formats in UTC', () => {
    const result = formatTenantDate('2026-04-09T12:00:00Z', 'UTC');
    expect(result).toContain('9');
    expect(result).toMatch(/abr/i);
  });

  it('formats in America/Lima', () => {
    const result = formatTenantDate('2026-04-09T00:00:00Z', 'America/Lima');
    expect(result).toContain('8');
  });

  it('accepts custom format', () => {
    const result = formatTenantDate('2026-04-09T12:00:00Z', 'UTC', 'yyyy-MM-dd');
    expect(result).toBe('2026-04-09');
  });
});

describe('formatTenantDateTime', () => {
  it('includes time component', () => {
    const result = formatTenantDateTime('2026-04-09T15:30:00Z', 'UTC');
    expect(result).toContain('15:30');
  });

  it('converts time to tenant timezone', () => {
    const result = formatTenantDateTime('2026-04-09T15:30:00Z', 'America/Lima');
    expect(result).toContain('10:30');
  });
});

describe('formatTenantTime', () => {
  it('shows only time', () => {
    const result = formatTenantTime('2026-04-09T15:30:00Z', 'UTC');
    expect(result).toBe('15:30');
  });

  it('converts to tenant timezone', () => {
    const result = formatTenantTime('2026-04-09T15:30:00Z', 'America/Lima');
    expect(result).toBe('10:30');
  });
});
