/**
 * Deliberately narrow: this project doesn't extend stylelint-config-standard
 * because the token boundary is the only thing we need Stylelint for. What
 * Stylelint's built-in rules can't express (raw numeric spacing/sizing
 * values, unknown/primitive var() misuse) is covered by the repository-owned
 * audit instead — see src/design-system/token-audit.ts.
 */
export default {
  rules: {
    "color-no-hex": true,
    "function-disallowed-list": ["rgb", "rgba", "hsl", "hsla"],
  },
  overrides: [
    {
      files: ["src/design-system/tokens/**/*.css"],
      rules: {
        "color-no-hex": null,
        "function-disallowed-list": null,
      },
    },
  ],
};
