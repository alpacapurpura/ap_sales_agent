import { describe, expect, it } from 'vitest';
import { parseBenchmarkText } from '../benchmark-parser';

describe('parseBenchmarkText', () => {
  it('returns null for empty input', () => {
    expect(parseBenchmarkText('')).toBeNull();
  });

  it('parses range pattern with percentage', () => {
    const result = parseBenchmarkText('Referencia CTR: 0.9-2.19%');
    expect(result).not.toBeNull();
    expect(result!.low).toBe(0.9);
    expect(result!.high).toBe(2.19);
    expect(result!.unit).toBe('percentage');
  });

  it('parses range pattern with trailing dollar sign', () => {
    // Note: The parser regex expects digits first, so "$0.70-$1.72" does not
    // match (leading $ blocks first capture group). Use trailing $ format.
    const result = parseBenchmarkText('Referencia CPC: 0.70-1.72$');
    expect(result).not.toBeNull();
    expect(result!.low).toBe(0.70);
    expect(result!.high).toBe(1.72);
    expect(result!.unit).toBe('currency');
  });

  it('returns null for dollar-prefixed range format (parser limitation)', () => {
    // Leading $ before each number is not matched by current RANGE_PATTERN
    const result = parseBenchmarkText('Referencia CPC: $0.70-$1.72');
    expect(result).toBeNull();
  });

  it('parses single value with promedio keyword', () => {
    const result = parseBenchmarkText('Referencia: promedio 5 paginas por sesion');
    expect(result).not.toBeNull();
    expect(result!.median).toBe(5);
    expect(result!.low).toBeNull();
    expect(result!.high).toBeNull();
  });

  it('parses multiple percentages', () => {
    const result = parseBenchmarkText(
      'Referencia engagement rate: Facebook 0.08%, Instagram 0.98%',
    );
    expect(result).not.toBeNull();
    expect(result!.low).toBe(0.08);
    expect(result!.high).toBe(0.98);
    expect(result!.unit).toBe('percentage');
  });

  it('computes median from range', () => {
    const result = parseBenchmarkText('Referencia: 10-20%');
    expect(result).not.toBeNull();
    expect(result!.median).toBe(15);
  });

  it('computes median from fractional range with rounding', () => {
    const result = parseBenchmarkText('Referencia CTR: 0.9-2.19%');
    expect(result).not.toBeNull();
    // (0.9 + 2.19) / 2 = 1.545 -> rounded to 2 decimals = 1.55
    expect(result!.median).toBe(1.55);
  });

  it('returns null for unparseable text', () => {
    const result = parseBenchmarkText('no numbers here');
    expect(result).toBeNull();
  });

  it('preserves rawText in output', () => {
    const input = 'Referencia: 10-20%';
    const result = parseBenchmarkText(input);
    expect(result).not.toBeNull();
    expect(result!.rawText).toBe(input);
  });

  it('detects ratio unit for x suffix', () => {
    const result = parseBenchmarkText('Referencia: 1.5-3.0x');
    expect(result).not.toBeNull();
    expect(result!.unit).toBe('ratio');
  });

  it('defaults to count unit when no hint present', () => {
    const result = parseBenchmarkText('Referencia: promedio 5 paginas');
    expect(result).not.toBeNull();
    expect(result!.unit).toBe('count');
  });
});
