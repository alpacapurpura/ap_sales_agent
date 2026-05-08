/**
 * ESLint rule: use-shell-mutex-for-drawer-toggles
 *
 * Warns when code calls `setSidebarState("collapsed" | "rail" | "full")`
 * directly. Drawer toggles MUST flow through `useShellMutex` to enforce
 * mutex policy across breakpoints (Story 1 T-4 mutex activation).
 *
 * Origin: T-7 (app-shell-sidebar-copilot-decoupling). Default level: warn
 * (ratchet to error post post-refactor stabilization).
 *
 * Allowed: setSidebarState calls inside `use-shell-mutex.ts` itself,
 * `SidebarContext.tsx`, and `CopilotSidebar.tsx` (legacy direct dispatch
 * is now wrapped by mutex but still uses setSidebarState internally).
 */
const ALLOWED_FILE_SUFFIXES = [
  "/hooks/use-shell-mutex.ts",
  "/components/shared/layout/SidebarContext.tsx",
  "/features/copilot/components/CopilotSidebar.tsx",
  "/features/copilot/store/copilot-store.ts",
];

const TARGET_VALUES = new Set(["collapsed", "rail", "full"]);

/** @type {import("eslint").Rule.RuleModule} */
export const useShellMutexForDrawerToggles = {
  meta: {
    type: "suggestion",
    docs: {
      description: "Prefer useShellMutex over direct setSidebarState dispatch.",
      recommended: false,
    },
    schema: [],
    messages: {
      preferMutex:
        "Direct setSidebarState({{value}}) — prefer useShellMutex.openPanel/closePanel for breakpoint-aware mutex policy.",
    },
  },
  create(context) {
    const filename = context.filename ?? context.getFilename?.() ?? "";
    if (ALLOWED_FILE_SUFFIXES.some((suffix) => filename.endsWith(suffix))) {
      return {};
    }
    return {
      CallExpression(node) {
        const callee = node.callee;
        if (callee.type !== "Identifier" || callee.name !== "setSidebarState") return;
        const arg = node.arguments[0];
        if (!arg) return;
        if (arg.type !== "Literal" || typeof arg.value !== "string") return;
        if (!TARGET_VALUES.has(arg.value)) return;
        context.report({
          node,
          messageId: "preferMutex",
          data: { value: JSON.stringify(arg.value) },
        });
      },
    };
  },
};
