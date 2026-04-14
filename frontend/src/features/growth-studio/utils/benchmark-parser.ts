/**
 * Parses free-text benchmark strings from the metric catalog into structured data.
 * Used as fallback when structured backend benchmarks aren't available.
 *
 * Examples of input strings:
 *   "Referencia CTR: 0.9-2.19% (Klipfolio)"
 *   "Referencia: promedio 5 paginas por sesion"
 *   "Referencia engagement rate: Facebook 0.08%, Instagram 0.98%"
 */

export interface ParsedBenchmark {
  low: number | null;
  high: number | null;
  median: number | null;
  unit: "percentage" | "currency" | "count" | "ratio";
  rawText: string;
}

const RANGE_PATTERN = /([\d.]+)\s*[-\u2013]\s*([\d.]+)\s*(%|x|\$)?/;
const SINGLE_VALUE_PATTERN =
  /(?:promedio|average|t\u00edpico|mean)\s*[:\s]?\s*\$?([\d.]+)\s*(%|x)?/i;
const PERCENTAGE_PATTERN = /([\d.]+)\s*%/g;

export function parseBenchmarkText(text: string): ParsedBenchmark | null {
  if (!text) return null;

  const cleaned = text.replace(/^Referencia[^:]*:\s*/i, "");

  // Try range pattern first (e.g., "0.9-2.19%")
  const rangeMatch = cleaned.match(RANGE_PATTERN);
  if (rangeMatch) {
    const low = parseFloat(rangeMatch[1]);
    const high = parseFloat(rangeMatch[2]);
    const unitHint = rangeMatch[3];
    const unit = detectUnit(unitHint, cleaned);
    return {
      low,
      high,
      median: Math.round(((low + high) / 2) * 100) / 100,
      unit,
      rawText: text,
    };
  }

  // Try single value (e.g., "promedio 5 paginas")
  const singleMatch = cleaned.match(SINGLE_VALUE_PATTERN);
  if (singleMatch) {
    const value = parseFloat(singleMatch[1]);
    const unitHint = singleMatch[2];
    const unit = detectUnit(unitHint, cleaned);
    return {
      low: null,
      high: null,
      median: value,
      unit,
      rawText: text,
    };
  }

  // Try extracting multiple percentages
  const percentages: number[] = [];
  let match;
  while ((match = PERCENTAGE_PATTERN.exec(cleaned)) !== null) {
    percentages.push(parseFloat(match[1]));
  }
  if (percentages.length >= 2) {
    const sorted = percentages.sort((a, b) => a - b);
    return {
      low: sorted[0],
      high: sorted[sorted.length - 1],
      median: Math.round(((sorted[0] + sorted[sorted.length - 1]) / 2) * 100) / 100,
      unit: "percentage",
      rawText: text,
    };
  }

  return null;
}

function detectUnit(
  hint: string | undefined,
  fullText: string,
): "percentage" | "currency" | "count" | "ratio" {
  if (hint === "%" || fullText.includes("%")) return "percentage";
  if (hint === "$" || fullText.includes("$")) return "currency";
  if (hint === "x" || fullText.includes("x ")) return "ratio";
  return "count";
}
