import postcss from "postcss";

import { allowedRawValues, layoutCustomProperties } from "./tokens/allowlist";
import { tokenNames } from "./tokens/tokens";

const layoutCustomPropertySet = new Set(layoutCustomProperties);

export interface AuditFinding {
  file: string;
  line: number;
  message: string;
}

const HEX_COLOR = /#[0-9a-fA-F]{3,8}\b/g;
const RAW_FUNCTIONAL_COLOR = /\b(?:rgba?|hsla?)\(\s*[0-9.]/g;
const RAW_LENGTH = /(?<![\w-])-?\d*\.?\d+(px|rem|em)\b/g;
const VAR_REFERENCE = /var\(\s*--([a-zA-Z0-9-]+)/g;

const allowedRawValueSet = new Set(allowedRawValues.map((entry) => entry.value));

function isAllowedLength(match: string): boolean {
  return allowedRawValueSet.has(match) || match === "0px" || match === "0rem" || match === "0em";
}

/**
 * A file is a "token source" file if it lives in design-system/tokens/ —
 * the only place primitive tokens may be defined and directly referenced.
 */
function isTokenSourceFile(filePath: string): boolean {
  return filePath.includes("design-system/tokens/");
}

/**
 * Audit one CSS source string. `filePath` is used only for allowlist
 * scoping and to label findings — callers decide which real files to scan.
 */
export function auditCssSource(source: string, filePath: string): AuditFinding[] {
  const findings: AuditFinding[] = [];
  const root = postcss.parse(source, { from: undefined });
  const tokenSource = isTokenSourceFile(filePath);

  root.walkDecls((decl) => {
    const line = decl.source?.start?.line ?? 0;
    const value = decl.value;

    if (!tokenSource) {
      const hexMatches = value.match(HEX_COLOR);
      if (hexMatches) {
        findings.push({ file: filePath, line, message: `raw hex color ${hexMatches[0]} outside the token layer (property: ${decl.prop})` });
      }
      if (RAW_FUNCTIONAL_COLOR.test(value)) {
        findings.push({ file: filePath, line, message: `raw rgb()/hsl() color literal outside the token layer (property: ${decl.prop})` });
      }
      RAW_FUNCTIONAL_COLOR.lastIndex = 0;

      const lengthMatches = value.match(RAW_LENGTH);
      if (lengthMatches) {
        for (const match of lengthMatches) {
          if (!isAllowedLength(match)) {
            findings.push({ file: filePath, line, message: `raw numeric visual value ${match} outside the token layer and not in the allowlist (property: ${decl.prop})` });
          }
        }
      }
    }

    let varMatch: RegExpExecArray | null;
    VAR_REFERENCE.lastIndex = 0;
    while ((varMatch = VAR_REFERENCE.exec(value))) {
      const name = varMatch[1];
      if (!name) continue;
      if (layoutCustomPropertySet.has(name)) continue;
      if (!tokenNames.has(name)) {
        findings.push({ file: filePath, line, message: `var(--${name}) is not a declared token (add it to tokens/tokens.ts alongside its CSS definition)` });
        continue;
      }
      if (!tokenSource && name.startsWith("kw-p-")) {
        findings.push({ file: filePath, line, message: `var(--${name}) is a primitive token used directly outside design-system/tokens/ — reference a semantic or component token instead (property: ${decl.prop})` });
      }
    }
  });

  return findings;
}
