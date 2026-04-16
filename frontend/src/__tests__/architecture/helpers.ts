/**
 * Architecture test helpers — filesystem scanning utilities.
 * Pattern from backend/tests/architecture/conftest.py
 */
import { fileURLToPath } from "url";
import * as fs from "fs";
import * as path from "path";

const _filename = fileURLToPath(import.meta.url);
const _dirname = path.dirname(_filename);

/** Absolute path to frontend/src/ */
export const SRC_DIR = path.resolve(_dirname, "../..");
export const FEATURES_DIR = path.join(SRC_DIR, "features");
export const SHARED_COMPONENTS_DIR = path.join(SRC_DIR, "components", "shared");

/** Path relative to SRC_DIR, using forward slashes. */
export function relPath(absPath: string): string {
  return path.relative(SRC_DIR, absPath).replace(/\\/g, "/");
}

/**
 * PascalCase: starts with uppercase, only letters and digits.
 * Single-segment only (no dots, no dashes).
 */
export function isPascalCase(name: string): boolean {
  return /^[A-Z][A-Za-z0-9]+$/.test(name);
}

/**
 * kebab-case: all lowercase letters/digits, separated by hyphens.
 * Single-segment only (no dots).
 */
export function isKebabCase(name: string): boolean {
  return /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/.test(name);
}

/**
 * Returns the first segment of a filename, stripping all extensions.
 * Matches ESLint check-file's `ignoreMiddleExtensions: true` behavior.
 * "puck.config.tsx" → "puck"
 * "use-audit.ts" → "use-audit"
 */
export function stemName(filename: string): string {
  return filename.split(".")[0];
}

/** Returns true if path is a test/mock file that should be excluded. */
export function isTestFile(filePath: string): boolean {
  const normalized = filePath.replace(/\\/g, "/");
  return (
    normalized.includes("/__tests__/") ||
    normalized.includes("/__mocks__/") ||
    normalized.endsWith(".test.ts") ||
    normalized.endsWith(".test.tsx") ||
    normalized.endsWith(".spec.ts") ||
    normalized.endsWith(".spec.tsx")
  );
}

/** Recursively list all files under a directory. */
export function walkFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  const result: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...walkFiles(full));
    } else if (entry.isFile()) {
      result.push(full);
    }
  }
  return result;
}

/** Recursively list all directories under a directory. */
export function walkDirs(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  const result: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      const full = path.join(dir, entry.name);
      result.push(full);
      result.push(...walkDirs(full));
    }
  }
  return result;
}

/** Top-level directory names under features/. */
export function getFeatureNames(): string[] {
  if (!fs.existsSync(FEATURES_DIR)) return [];
  return fs
    .readdirSync(FEATURES_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

/** Top-level folder names directly inside a feature directory. */
export function getFeatureTopDirs(featureName: string): string[] {
  const dir = path.join(FEATURES_DIR, featureName);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

/** Read file content as UTF-8 string. Returns empty string if unreadable. */
export function readFile(filePath: string): string {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "";
  }
}
