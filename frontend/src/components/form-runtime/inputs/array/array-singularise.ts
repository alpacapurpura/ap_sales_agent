/**
 * Derives an approximate Spanish singular from a plural noun for use in
 * "Agregar {noun}" / "Nuevo {noun}…" copy. Best-effort — covers the
 * common Spanish rules:
 *
 * - ends in `ces` (consonant transformation) → swap to `z`
 *   ("luces" → "luz")
 * - ends in `es` after a consonant → strip `es`
 *   ("pilares" → "pilar", "canales" → "canal")
 * - ends in `s` after a vowel → strip `s`
 *   ("casos" → "caso", "testimonios" → "testimonio")
 * - otherwise → unchanged
 *
 * Known edge: loses accents on transformations like "integraciones" →
 * "integracion". Schemas with accented singulars should declare an
 * explicit `itemSchema.itemNoun` override instead of relying on this util.
 */
export function singulariseES(word: string): string {
  const w = word.trim().toLowerCase();
  if (w.length <= 2) return w;

  if (w.endsWith("ces") && w.length > 3) {
    return `${w.slice(0, -3)}z`;
  }

  if (w.endsWith("es") && w.length > 3) {
    const stem = w.slice(0, -2);
    const last = stem[stem.length - 1];
    const consonants = "bcdfghjklmnpqrstvwxyz";
    if (consonants.includes(last)) return stem;
    // ends in `es` but preceded by vowel (rare) — fall back to dropping `s`
    return w.slice(0, -1);
  }

  if (w.endsWith("s")) return w.slice(0, -1);

  return w;
}
