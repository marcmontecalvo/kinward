// @ts-check
// Uses @babel/eslint-parser rather than typescript-eslint: typescript-eslint's
// typescript-estree caps its `typescript` peer range below 6.1 and crashes at
// import time against TypeScript 7 (this project's pinned, non-negotiable
// version — see AGENTS.md "do not downgrade the build stack"). Babel's parser
// only strips TS syntax for parsing; it has no dependency on the `typescript`
// package's compiler API, so it isn't exposed to that incompatibility. This
// rule is a pure AST syntax check and needs no type information anyway.
import babelParser from "@babel/eslint-parser";

const layoutAdapterPath = "src/surfaces/layoutStyleAdapter.tsx";

const noInlineStyleRule = {
  selector: "JSXAttribute[name.name='style']",
  message:
    "Inline JSX style props bypass the token system. Compose a semantic/component class from design-system/tokens instead. " +
    "The one exception is the audited layout-style adapter (src/surfaces/layoutStyleAdapter.tsx), which may set only the " +
    "declared layout custom properties (grid column/row/count/gap) — never general visual styles.",
};

export default [
  { ignores: ["dist/**", "node_modules/**", "playwright-report/**", "test-results/**"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: babelParser,
      parserOptions: {
        requireConfigFile: false,
        babelOptions: {
          presets: ["@babel/preset-typescript", "@babel/preset-react"],
        },
      },
    },
    rules: {
      "no-restricted-syntax": ["error", noInlineStyleRule],
    },
  },
  {
    files: [layoutAdapterPath],
    rules: {
      "no-restricted-syntax": "off",
    },
  },
];
