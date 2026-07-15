import { surfaceLayoutSchema, type SurfaceClass, type SurfaceLayout } from "@kinward/schemas";

const cards = {
  presence: { id: "presence-example", type: "assistant-presence", version: 1, title: "Assistant presence", config: {} },
  now: { id: "now-example", type: "now", version: 1, title: "Now", config: {} },
  briefing: { id: "briefing-example", type: "briefing", version: 1, title: "Briefing", config: {} },
  continuing: { id: "continue-example", type: "continue", version: 1, title: "Continue", config: {} },
  schedule: { id: "schedule-example", type: "schedule", version: 1, title: "Schedule", config: {} },
  house: { id: "house-example", type: "house-status", version: 1, title: "House status", config: {} },
  approval: { id: "approval-example", type: "approval", version: 1, title: "Approval", config: {} },
  input: { id: "input-example", type: "assistant-input", version: 1, title: "Assistant input", config: {} },
} as const;

const place = (card: typeof cards[keyof typeof cards], column: number, row: number, columns: number, rows: number) => ({ ...card, column, row, columns, rows });

function layout(id: string, surfaceClass: SurfaceClass, columns: number, instances: readonly ReturnType<typeof place>[]): SurfaceLayout {
  return surfaceLayoutSchema.parse({ schemaMajor: 1, id, version: 1, contextVersion: 1, surfaceClass, grid: { columns, gapPx: 16 }, instances });
}

export const productLayouts: Readonly<Record<SurfaceClass, SurfaceLayout>> = Object.freeze({
  "personal-mobile": layout("product-personal-mobile", "personal-mobile", 4, [place(cards.presence, 1, 1, 4, 1), place(cards.now, 1, 2, 4, 2), place(cards.briefing, 1, 4, 4, 2), place(cards.continuing, 1, 6, 4, 2), place(cards.schedule, 1, 8, 4, 2), place(cards.house, 1, 10, 4, 2), place(cards.approval, 1, 12, 4, 3), place(cards.input, 1, 15, 4, 1)]),
  "personal-tablet": layout("product-personal-tablet", "personal-tablet", 8, [place(cards.presence, 1, 1, 8, 1), place(cards.now, 1, 2, 5, 2), place(cards.briefing, 6, 2, 3, 2), place(cards.continuing, 1, 4, 4, 2), place(cards.schedule, 5, 4, 4, 2), place(cards.house, 1, 6, 4, 2), place(cards.approval, 5, 6, 4, 3), place(cards.input, 1, 9, 8, 1)]),
  "personal-desktop": layout("product-personal-desktop", "personal-desktop", 12, [place(cards.presence, 1, 1, 12, 1), place(cards.now, 1, 2, 7, 2), place(cards.briefing, 8, 2, 5, 2), place(cards.continuing, 1, 4, 4, 2), place(cards.schedule, 5, 4, 4, 2), place(cards.house, 9, 4, 4, 2), place(cards.approval, 1, 6, 6, 3), place(cards.input, 1, 9, 12, 1)]),
  "shared-kitchen": layout("product-shared-kitchen", "shared-kitchen", 12, [place(cards.presence, 1, 1, 12, 1), place(cards.now, 1, 2, 7, 3), place(cards.briefing, 8, 2, 5, 3), place(cards.schedule, 1, 5, 6, 3), place(cards.house, 7, 5, 6, 3), place(cards.approval, 1, 8, 12, 3), place(cards.continuing, 1, 11, 6, 2), place(cards.input, 7, 11, 6, 2)]),
  "shared-living-room": layout("product-shared-living-room", "shared-living-room", 12, [place(cards.presence, 1, 1, 12, 1), place(cards.now, 1, 2, 8, 3), place(cards.house, 9, 2, 4, 3), place(cards.briefing, 1, 5, 7, 3), place(cards.approval, 8, 5, 5, 3), place(cards.schedule, 1, 8, 4, 2), place(cards.continuing, 5, 8, 4, 2), place(cards.input, 9, 8, 4, 2)]),
});
