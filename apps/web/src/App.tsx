import { getCard } from "./cards/registry";

const cards = [
  {
    id: "now",
    type: "now",
    title: "Now",
    className: "now-card",
    data: {
      headline: "Your evening is clear until 6:30.",
      detail: "Dinner shifted later and does not conflict with your calendar.",
      action: "Review change",
    },
  },
  {
    id: "briefing",
    type: "list",
    title: "Quiet briefing",
    data: {
      items: [
        "The school calendar added an early-release day next Friday.",
        "The garage door was closed automatically.",
        "No approvals are waiting.",
      ],
    },
  },
  {
    id: "continue",
    type: "topics",
    title: "Continue",
    data: { items: ["Summer trip", "Kitchen project", "Vehicle maintenance"] },
  },
  {
    id: "house",
    type: "now",
    title: "House status",
    data: {
      headline: "All normal",
      detail: "3 people home · doors secure · no active alerts",
    },
  },
] as const;

export function App() {
  return (
    <main className="shell">
      <header className="assistant-header">
        <div>
          <p className="eyebrow">Kinward Assistant</p>
          <h1>Good afternoon.</h1>
          <p className="muted">Nothing urgent needs your attention.</p>
        </div>
        <button className="avatar" aria-label="Open assistant">K</button>
      </header>

      <section className="grid" aria-label="Your assistant overview">
        {cards.map((card) => {
          const definition = getCard(card.type);
          const Card = definition.render;
          return <Card key={card.id} title={card.title} data={card.data} className={card.className} />;
        })}
      </section>

      <form className="composer" onSubmit={(event) => event.preventDefault()}>
        <label className="sr-only" htmlFor="assistant-input">Ask Kinward</label>
        <input id="assistant-input" placeholder="Ask, do, remember, or explain…" />
        <button type="submit">Send</button>
      </form>
    </main>
  );
}
