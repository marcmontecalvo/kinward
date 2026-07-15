import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Setup } from "./Setup";

describe("household setup", () => {
  it("renders an ordinary-language keyboard form without technical integrations", () => {
    const markup = renderToStaticMarkup(<Setup />);
    expect(markup).toContain("Private household setup");
    expect(markup).toContain("One-time setup authorization");
    expect(markup).toContain("Add another adult");
    expect(markup).toContain("Add another child");
    expect(markup).toContain("Add another pet");
    expect(markup).toContain("Pets receive no account");
    expect(markup).not.toContain("Home Assistant");
    expect(markup).not.toContain("provider");
    expect(markup).not.toContain("tenant");
  });
});
