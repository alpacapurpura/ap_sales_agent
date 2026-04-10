/**
 * Recursive snake_case ↔ camelCase conversion utilities.
 *
 * Use these in API fetchers when the backend sends snake_case keys but the
 * TypeScript types/components expect camelCase. Extracted from the advertising
 * module so other features can reuse it and stay consistent.
 */

export function snakeToCamel(s: string): string {
  return s.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
}

export function camelToSnake(s: string): string {
  return s.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Recursively convert every key in an object/array tree from snake_case to
 * camelCase. Leaves primitive values untouched.
 */
export function camelizeKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map(item => camelizeKeys<unknown>(item)) as T;
  }
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      result[snakeToCamel(key)] = camelizeKeys(value);
    }
    return result as T;
  }
  return obj as T;
}

/**
 * Recursively convert every key in an object/array tree from camelCase to
 * snake_case. Use when sending payloads to endpoints that expect snake_case.
 */
export function snakeifyKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map(item => snakeifyKeys<unknown>(item)) as T;
  }
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      result[camelToSnake(key)] = snakeifyKeys(value);
    }
    return result as T;
  }
  return obj as T;
}
