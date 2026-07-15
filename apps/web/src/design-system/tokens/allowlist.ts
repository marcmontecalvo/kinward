/**
 * The ONLY legitimate way to permit a raw visual value outside the token
 * layer. There is no inline-disable escape hatch for the token audit,
 * Stylelint, or ESLint token rules — every exception must be a named,
 * documented entry here, so it shows up in code review as a real diff to
 * this file rather than a silently suppressed warning at the call site.
 *
 * Each entry must justify itself: why the value is a structural necessity
 * rather than a design decision that belongs in a token.
 */

export interface AllowlistEntry {
  /** Exact raw value or a short regex-safe pattern fragment. */
  value: string;
  reason: string;
}

export const allowedRawValues: readonly AllowlistEntry[] = [
  { value: "0", reason: "Zero is dimensionless; there is no design decision to token." },
  { value: "100%", reason: "Full-bleed sizing; not a scale choice." },
  { value: "currentColor", reason: "Inherits from an already-tokenized color; introduces no new value." },
  { value: "inherit", reason: "Explicit inheritance; introduces no new value." },
  { value: "none", reason: "Explicit absence of a value (e.g. list-style, box-shadow)." },
  { value: "transparent", reason: "Structural transparency, aliased from kw-p-color-transparent where a color is expected." },
  { value: "rect(0,0,0,0)", reason: "The standard sr-only screen-reader clipping rect; not a visual design value." },
  { value: "rect(0, 0, 0, 0)", reason: "The standard sr-only screen-reader clipping rect (spaced variant)." },
  { value: "1px", reason: "The sr-only technique's 1x1px hidden box; not a visual sizing decision." },
  { value: "-1px", reason: "The sr-only technique's negative margin, paired with the 1px hidden box; not a visual sizing decision." },
  { value: "0.01ms", reason: "The reduced-motion 'effectively instant' technique; exactly 0 can suppress transitionend events some browsers rely on. A technical necessity, not a design decision." },
];

/**
 * File-scoped exception: the audited layout-style adapter is the one place
 * allowed to set inline styles, and only for the declared layout custom
 * properties (grid column/row/count/gap) — never general visual styles.
 * Keep this path in sync with the file created in the surface-shell task.
 */
export const layoutStyleAdapterPath = "src/surfaces/layoutStyleAdapter.tsx";

/**
 * The exact set of custom properties layoutStyleAdapter.tsx is allowed to
 * produce. These are deliberately NOT in tokens.ts: they're data-driven
 * runtime values (a resolved layout's column/row/count/gap), not designer
 * scale choices, so they don't belong in the token vocabulary. The token
 * audit allows var() references to exactly these names without requiring
 * a tokens.ts entry — adding a new name here is how you'd extend what the
 * adapter may set, and it's the only way to do it.
 */
export const layoutCustomProperties: readonly string[] = [
  "kw-layout-columns",
  "kw-layout-gap",
  "kw-layout-column-start",
  "kw-layout-column-span",
  "kw-layout-row-start",
  "kw-layout-row-span",
];
