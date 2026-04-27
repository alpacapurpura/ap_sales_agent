/**
 * Dot-notation path helpers for nested form-runtime values.
 *
 * Section schemas declare fields with paths like ``demographics.age_range``
 * to mirror the JSONB sub-key shape used by the backend (BuyerPersona,
 * BrandSettings, …). Reading and writing those paths must traverse into
 * nested objects rather than treating the dotted string as a literal flat
 * key — the latter silently breaks the round-trip because the backend's
 * Pydantic DTO declares typed nested fields and ignores unknown extras.
 */

type AnyRecord = Record<string, unknown>;

function isPlainObject(value: unknown): value is AnyRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Read a value from ``obj`` by dot-notation ``path``.
 *
 * Returns ``undefined`` when any intermediate segment is missing or not a
 * plain object — keeps the call site free of optional-chaining noise.
 */
export function getNestedPath<T = unknown>(obj: object, path: string): T | undefined {
  if (!path) return undefined;
  if (!path.includes(".")) {
    return (obj as AnyRecord)[path] as T | undefined;
  }
  let cursor: unknown = obj;
  for (const segment of path.split(".")) {
    if (!isPlainObject(cursor)) return undefined;
    cursor = cursor[segment];
  }
  return cursor as T | undefined;
}

/**
 * Return a shallow-cloned copy of ``obj`` with ``value`` written at ``path``.
 *
 * Cloning is path-local: only the objects on the touched path are cloned,
 * sibling references are preserved (cheap immutable update suitable for
 * React state). Intermediate non-object values are replaced with a fresh
 * dict so legacy/corrupt data cannot block the write.
 */
export function setNestedPath<T extends object>(obj: T, path: string, value: unknown): T {
  if (!path) return obj;
  if (!path.includes(".")) {
    return { ...(obj as AnyRecord), [path]: value } as T;
  }
  const segments = path.split(".");
  const next: AnyRecord = { ...(obj as AnyRecord) };
  let cursor: AnyRecord = next;
  for (let i = 0; i < segments.length - 1; i++) {
    const key = segments[i];
    const child = cursor[key];
    cursor[key] = isPlainObject(child) ? { ...child } : {};
    cursor = cursor[key] as AnyRecord;
  }
  cursor[segments[segments.length - 1]] = value;
  return next as T;
}
