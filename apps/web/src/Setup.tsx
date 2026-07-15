import { type FormEvent, useMemo, useState } from "react";

type SetupOutcome = { kind: "idle" | "working" | "success" | "error"; message: string };

export function Setup() {
  const csrf = useMemo(() => crypto.randomUUID() + crypto.randomUUID(), []);
  const requestIdentity = useMemo(() => crypto.randomUUID(), []);
  const [outcome, setOutcome] = useState<SetupOutcome>({ kind: "idle", message: "" });
  const [adultRows, setAdultRows] = useState([0]);
  const [childRows, setChildRows] = useState([0]);
  const [petRows, setPetRows] = useState([0]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOutcome({ kind: "working", message: "Creating your household securely…" });
    const form = new FormData(event.currentTarget);
    const authorization = String(form.get("setupAuthorization") ?? "");
    const optional = (name: string) => String(form.get(name) ?? "").trim();
    const profiles = [
      ...form.getAll("adultName").map(String).map((display_name) => ({ display_name: display_name.trim(), kind: "adult" })),
      ...form.getAll("childName").map(String).map((display_name) => ({ display_name: display_name.trim(), kind: "child" })),
    ].filter((profile) => profile.display_name);
    const pets = petRows.flatMap((row) => {
      const display_name = optional(`petName-${row}`);
      if (!display_name) return [];
      const careFact = optional(`petCareFact-${row}`);
      return [{ display_name, species: optional(`petSpecies-${row}`), shared_facts: careFact ? [careFact] : [] }];
    });
    const payload = {
      household_name: String(form.get("householdName") ?? ""),
      admin_name: String(form.get("adminName") ?? ""),
      admin_email: String(form.get("email") ?? ""),
      password: String(form.get("password") ?? ""),
      assistant_name: String(form.get("assistantName") ?? ""),
      fallback_assistant_name: "Kinward",
      profiles,
      pets,
      csrf_token: csrf,
    };
    try {
      const response = await fetch("/api/v1/setup/household", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Setup-Authorization": authorization,
          "X-CSRF-Token": csrf,
          "Idempotency-Key": requestIdentity,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        setOutcome({ kind: "error", message: "Setup was not completed. Check the details and try again safely." });
        return;
      }
      setOutcome({ kind: "success", message: "Your household is ready. The setup authorization can no longer be used." });
      event.currentTarget.reset();
    } catch {
      setOutcome({ kind: "error", message: "Kinward could not be reached. No partial setup was accepted." });
    }
  }

  return (
    <main className="setup-shell">
      <header>
        <p className="eyebrow">Private household setup</p>
        <h1>Welcome to Kinward.</h1>
        <p className="muted">Create one household, your administrator account, and its two foundational assistants.</p>
      </header>
      <form className="setup-form" onSubmit={(event) => void submit(event)}>
        <label>Household name<input name="householdName" required maxLength={120} autoComplete="organization" placeholder="Example Household" /></label>
        <label>Your name<input name="adminName" required maxLength={120} autoComplete="name" placeholder="Example Adult" /></label>
        <label>Email<input name="email" required type="email" autoComplete="email" placeholder="adult@example.invalid" /></label>
        <label>Password<input name="password" required type="password" minLength={12} autoComplete="new-password" /></label>
        <label>Personal assistant name<input name="assistantName" required maxLength={120} placeholder="Atlas Example" /></label>
        <fieldset>
          <legend>Optional household profiles</legend>
          {adultRows.map((row) => <label key={`adult-${row}`}>Another adult<input name="adultName" maxLength={120} placeholder="Example Grownup" /></label>)}
          <button type="button" onClick={() => setAdultRows((rows) => [...rows, rows.length])}>Add another adult</button>
          {childRows.map((row) => <label key={`child-${row}`}>A child<input name="childName" maxLength={120} placeholder="Example Child" /></label>)}
          <button type="button" onClick={() => setChildRows((rows) => [...rows, rows.length])}>Add another child</button>
        </fieldset>
        <fieldset>
          <legend>Optional pet profile</legend>
          {petRows.map((row) => (
            <div className="setup-pet" key={`pet-${row}`}>
              <label>Pet name<input name={`petName-${row}`} maxLength={120} placeholder="Example Pet" /></label>
              <label>Species<input name={`petSpecies-${row}`} maxLength={80} placeholder="robot dog" /></label>
              <label>Household-shared care fact<input name={`petCareFact-${row}`} maxLength={200} placeholder="Uses the fictional blue bowl" /></label>
            </div>
          ))}
          <button type="button" onClick={() => setPetRows((rows) => [...rows, rows.length])}>Add another pet</button>
          <p className="muted">Pets receive no account, assistant, private memory, credentials, approvals, or action authority.</p>
        </fieldset>
        <label>One-time setup authorization<input name="setupAuthorization" required type="password" minLength={24} autoComplete="off" /></label>
        <button type="submit" disabled={outcome.kind === "working"}>Create household</button>
        <p role="status" aria-live="polite" className={outcome.kind === "error" ? "error" : "muted"}>{outcome.message}</p>
      </form>
    </main>
  );
}
