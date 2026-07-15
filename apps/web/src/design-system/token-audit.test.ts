import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { auditCssSource } from "./token-audit";

const APP_FILE = "src/App.css";
const TOKEN_FILE = "src/design-system/tokens/semantic.css";

describe("auditCssSource — negative fixtures (representative forbidden values must fail)", () => {
  it("flags a raw hex color outside the token layer", () => {
    const findings = auditCssSource(".card { color: #ff00aa; }", APP_FILE);
    expect(findings.some((f) => f.message.includes("#ff00aa"))).toBe(true);
  });

  it("flags a raw rgba() color literal outside the token layer", () => {
    const findings = auditCssSource(".card { background: rgba(10, 20, 30, 0.5); }", APP_FILE);
    expect(findings.some((f) => f.message.includes("rgb()/hsl()"))).toBe(true);
  });

  it("flags a raw non-allowlisted px length outside the token layer", () => {
    const findings = auditCssSource(".card { padding: 17px; }", APP_FILE);
    expect(findings.some((f) => f.message.includes("17px"))).toBe(true);
  });

  it("flags a primitive token referenced directly outside design-system/tokens/", () => {
    const findings = auditCssSource(".card { color: var(--kw-p-color-clay-600); }", APP_FILE);
    expect(findings.some((f) => f.message.includes("primitive token used directly"))).toBe(true);
  });

  it("flags an undeclared/unknown custom property", () => {
    const findings = auditCssSource(".card { color: var(--kw-totally-made-up); }", APP_FILE);
    expect(findings.some((f) => f.message.includes("not a declared token"))).toBe(true);
  });

  it("does not flag allowlisted structural values", () => {
    const findings = auditCssSource(
      ".sr-only { padding: 0; width: 100%; clip: rect(0, 0, 0, 0); } .x { color: currentColor; outline: inherit; box-shadow: none; }",
      APP_FILE,
    );
    expect(findings).toEqual([]);
  });

  it("does not flag the audited layout adapter's declared custom properties", () => {
    const findings = auditCssSource(".resolved-grid { grid-template-columns: repeat(var(--kw-layout-columns), minmax(0, 1fr)); gap: var(--kw-layout-gap); }", "src/surfaces/layoutStyleAdapter.css");
    expect(findings).toEqual([]);
  });

  it("does not flag a legitimate semantic-token reference", () => {
    const findings = auditCssSource(".card { color: var(--kw-color-text-primary); }", APP_FILE);
    expect(findings).toEqual([]);
  });

  it("allows raw values inside the token source layer itself", () => {
    const findings = auditCssSource(":root { --kw-p-color-clay-600: #a66b52; }", TOKEN_FILE);
    expect(findings).toEqual([]);
  });
});

describe("real repository scan", () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const srcRoot = join(here, "..");

  function collectCssFiles(dir: string): string[] {
    const entries = readdirSync(dir);
    return entries.flatMap((entry: string) => {
      const full = join(dir, entry);
      const stats = statSync(full);
      if (stats.isDirectory()) return collectCssFiles(full);
      return full.endsWith(".css") ? [full] : [];
    });
  }

  it("finds zero token-boundary violations across application CSS", () => {
    const files = collectCssFiles(srcRoot).filter((file) => !file.includes(`${join("design-system", "tokens")}`));
    const allFindings = files.flatMap((file) => {
      const source = readFileSync(file, "utf8");
      const relPath = relative(join(srcRoot, ".."), file);
      return auditCssSource(source, relPath);
    });
    if (allFindings.length > 0) {
      const report = allFindings.map((f) => `${f.file}:${f.line} — ${f.message}`).join("\n");
      throw new Error(`Token audit found violations:\n${report}`);
    }
    expect(allFindings).toEqual([]);
  });
});
