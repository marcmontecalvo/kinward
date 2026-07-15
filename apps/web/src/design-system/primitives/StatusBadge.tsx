import type { CardState } from "@kinward/schemas";

const stateLabels: Record<CardState, string> = {
  available: "Available",
  empty: "Nothing to show",
  loading: "Loading",
  degraded: "Limited",
  unavailable: "Unavailable",
  stale: "May be out of date",
  error: "Could not load",
};

export type StatusBadgeProps = {
  state: CardState;
  message: string;
};

/**
 * Every state is distinguished by a glyph (via the `state-*` CSS classes'
 * ::before content) AND a text label — never by color alone, and never by
 * the glyph alone either, since `role="status"` needs real text for
 * assistive tech.
 */
export function StatusBadge({ state, message }: StatusBadgeProps) {
  return (
    <span className={`state state-${state}`} role="status">
      {stateLabels[state]}: {message}
    </span>
  );
}
