type CardProps = {
  title: string;
  children: React.ReactNode;
  className?: string;
};

function Card({ title, children, className = "" }: CardProps) {
  return (
    <section className={`card ${className}`.trim()}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

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
        <Card title="Now" className="now-card">
          <p className="headline">Your evening is clear until 6:30.</p>
          <p className="muted">Dinner shifted later and does not conflict with your calendar.</p>
          <button>Review change</button>
        </Card>

        <Card title="Quiet briefing">
          <ul>
            <li>The school calendar added an early-release day next Friday.</li>
            <li>The garage door was closed automatically.</li>
            <li>No approvals are waiting.</li>
          </ul>
        </Card>

        <Card title="Continue">
          <div className="topic-list">
            <button>Summer trip</button>
            <button>Kitchen project</button>
            <button>Vehicle maintenance</button>
          </div>
        </Card>

        <Card title="House status">
          <p className="headline">All normal</p>
          <p className="muted">3 people home · doors secure · no active alerts</p>
        </Card>
      </section>

      <form className="composer" onSubmit={(event) => event.preventDefault()}>
        <label className="sr-only" htmlFor="assistant-input">Ask Kinward</label>
        <input id="assistant-input" placeholder="Ask, do, remember, or explain…" />
        <button type="submit">Send</button>
      </form>
    </main>
  );
}
