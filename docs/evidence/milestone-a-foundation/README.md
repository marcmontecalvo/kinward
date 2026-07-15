# Milestone A Five-Surface Foundation Evidence

This package is a **mock-backed foundation**. It proves the registry, declarative layout,
policy-filtering, responsive, and automated accessibility foundations for personal mobile,
tablet, desktop, shared kitchen, and shared living-room contexts. It does not claim live
Milestone B capabilities.

Run the reproducible evidence suite with:

```bash
pnpm --filter @kinward/web exec playwright install chromium
make browser-test
```

The suite starts a production-equivalent Vite surface with fictional adapters, generates ignored
local reports under `test-results/`, and stores failure-only screenshots and traces outside version
control. The committed manifest records the reference browser, viewport, device scale, test hash,
coverage, and safety disposition without recording a machine hostname, local path, private URL,
database, credential, or household data.

The 1920×1080 Chromium reference is a deterministic geometry and semantics proxy for the documented
21.5-inch shared display at 1.5 m. It checks room typography, target size/spacing, contrast, reflow,
and scaling. It is not the Milestone C physical human-inspection freeze; that remains explicitly
unproven until performed in the frozen target environment.

The suite must finish with all runnable tests passing. The mobile project intentionally skips the
desktop-only fixed-reference audit; it runs the remaining context, privacy, responsive, keyboard,
and accessibility checks.
