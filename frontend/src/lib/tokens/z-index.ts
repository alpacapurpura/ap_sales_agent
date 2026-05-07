/**
 * Z-index SSoT — all shell z-index values defined here.
 *
 * Layer scale uses multiples of 10 for flexibility.
 * Import Z_INDEX for numeric values, Z_INDEX_CLASSES for Tailwind
 * arbitrary-value class strings.
 *
 * AD5: fluid scale 0/10/.../100 with spacing 10 between layers.
 */
export const Z_INDEX = Object.freeze({
  /** Normal document flow */
  AUTO: "auto",
  /** Regular content */
  CONTENT: 0,
  /** Sticky headers/footers within scrollable areas */
  STICKY: 10,
  /** App sidebar (desktop fixed left panel) */
  APP_SIDEBAR: 40,
  /** Topbar (mobile top navigation bar) */
  TOPBAR: 50,
  /** Copilot backdrop scrim (mobile overlay behind drawer) */
  COPILOT_BACKDROP: 50,
  /** Copilot drawer (mobile right panel) */
  COPILOT_DRAWER: 60,
  /** App sidebar mobile drawer */
  APP_SIDEBAR_DRAWER: 60,
  /** Floating action button (mobile bottom-right) */
  FAB: 70,
  /** Modal dialogs */
  MODAL: 80,
  /** Dropdown menus */
  DROPDOWN: 85,
  /** Tooltip overlays */
  TOOLTIP: 90,
  /** Toast notifications */
  TOAST: 100,
} as const);

export type ZIndexKey = keyof typeof Z_INDEX;
export type ZIndexValue = (typeof Z_INDEX)[ZIndexKey];

/**
 * Tailwind arbitrary-value class strings for each z-index token.
 * Use these when applying z-index via className.
 *
 * Example: className={Z_INDEX_CLASSES.COPILOT_DRAWER}
 */
export const Z_INDEX_CLASSES = Object.freeze({
  AUTO: "z-auto",
  CONTENT: "z-0",
  STICKY: "z-10",
  APP_SIDEBAR: "z-[40]",
  TOPBAR: "z-[50]",
  COPILOT_BACKDROP: "z-[50]",
  COPILOT_DRAWER: "z-[60]",
  APP_SIDEBAR_DRAWER: "z-[60]",
  FAB: "z-[70]",
  MODAL: "z-[80]",
  DROPDOWN: "z-[85]",
  TOOLTIP: "z-[90]",
  TOAST: "z-[100]",
} as const satisfies Record<ZIndexKey, string>);
