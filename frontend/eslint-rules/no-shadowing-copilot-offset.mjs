/**
 * ESLint rule: no-shadowing-copilot-offset
 *
 * Forbids importing `useCopilotOffset` from any path other than the canonical
 * SSoT module:
 *   - `@/hooks/use-copilot-offset` (canonical)
 *   - `@/features/copilot/lib/copilot-shell-widths` (re-exports allowed)
 *
 * Origin: T-7 (app-shell-sidebar-copilot-decoupling). AD6 — single source of
 * truth for `useCopilotOffset` prevents drift across consumers.
 *
 * Default level: error. Replicates `test-no-shadowing-copilot-offset.test.ts`
 * arch-fitness logic at lint time for faster feedback.
 */
const ALLOWED_SOURCES = [
  "@/hooks/use-copilot-offset",
  "@/features/copilot/lib/copilot-shell-widths",
];

/** @type {import("eslint").Rule.RuleModule} */
export const noShadowingCopilotOffset = {
  meta: {
    type: "problem",
    docs: {
      description: "Forbid importing useCopilotOffset from non-canonical paths.",
      recommended: true,
    },
    schema: [],
    messages: {
      forbidden:
        "Import 'useCopilotOffset' from '@/hooks/use-copilot-offset' (canonical SSoT). Got: '{{source}}'.",
    },
  },
  create(context) {
    return {
      ImportDeclaration(node) {
        const source = node.source.value;
        if (typeof source !== "string") return;
        const importsHook = node.specifiers.some(
          (spec) =>
            spec.type === "ImportSpecifier" &&
            spec.imported.type === "Identifier" &&
            spec.imported.name === "useCopilotOffset",
        );
        if (!importsHook) return;
        if (ALLOWED_SOURCES.includes(source)) return;
        context.report({ node, messageId: "forbidden", data: { source } });
      },
    };
  },
};
