#!/usr/bin/env node
// Tests of the style checks: stylelint rejects raw design values outside
// the tokens file, accepts tokens, and the inline-style check rejects
// <style> blocks and style= attributes.
//
// Usage: node scripts/test-style-checks.mjs CSS_PROBE_PATH [TOKENS_PATH | -]
// TOKENS_PATH is the tokens file that the stylelint configuration exempts;
// "-" skips that test in a repository without a tokens file.

import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import stylelint from "stylelint";

const [probePath, tokensPath] = process.argv.slice(2);
let failures = 0;

function check(name, ok) {
  console.log(`${ok ? "ok  " : "FAIL"} ${name}`);
  if (!ok) failures += 1;
}

async function lint(code, codeFilename) {
  const result = await stylelint.lint({ code, codeFilename });
  return result.results[0].warnings.map((w) => w.rule);
}

const rejected = [
  ["color: #123456", "color-no-hex"],
  ["color: red", "color-named"],
  ["background: rgba(0, 0, 0, 0.5)", "function-disallowed-list"],
  ["background: hsl(10 20% 30%)", "function-disallowed-list"],
  ["font-size: 15px", "declaration-property-value-allowed-list"],
  ["font-size: 1rem", "declaration-property-value-allowed-list"],
  ["font-weight: 650", "declaration-property-value-allowed-list"],
  ["border-radius: 7px", "declaration-property-value-allowed-list"],
  ["box-shadow: 0 1px 2px var(--bas-shadow)", "declaration-property-value-allowed-list"],
  ["padding: 10px", "declaration-property-value-allowed-list"],
  ["margin: 1rem 0", "declaration-property-value-allowed-list"],
  ["gap: 18px", "declaration-property-value-allowed-list"],
  ["padding-left: var(--other-space)", "declaration-property-value-allowed-list"],
];
for (const [decl, rule] of rejected) {
  const rules = await lint(`.probe { ${decl}; }\n`, probePath);
  check(`rejects "${decl}" (${rule})`, rules.includes(rule));
}

const accepted = [
  "color: var(--bas-text)",
  "font-size: var(--bas-text-sm)",
  "font-weight: var(--bas-weight-bold)",
  "border-radius: var(--bas-radius-pill)",
  "border-radius: 0",
  "box-shadow: var(--bas-shadow-card)",
  "box-shadow: none",
  "padding: var(--bas-space-2) var(--bas-control-px-sm)",
  "margin: 0 auto var(--bas-gap-section)",
  "gap: var(--bas-gap-related)",
  "font-size: inherit",
];
for (const decl of accepted) {
  const rules = await lint(`.probe { ${decl}; }\n`, probePath);
  check(`accepts "${decl}"`, rules.length === 0);
}

if (tokensPath && tokensPath !== "-") {
  const tokenRules = await lint(":root { --bas-x: #123456; --bas-y: rgba(0, 0, 0, 0.5); }\n.x { font-size: 15px; }\n", tokensPath);
  check("the tokens file may hold raw values", tokenRules.length === 0);
}

const dir = mkdtempSync(join(tmpdir(), "bas-inline-"));
const cases = [
  ["attr.html", '<p style="color: red">x</p>\n', false],
  ["block.php", "<?php ?>\n<style>p { color: red; }</style>\n", false],
  ["clean.html", '<p class="bas-site-footer">x</p>\n', true],
];
for (const [name, content, shouldPass] of cases) {
  const file = join(dir, name);
  writeFileSync(file, content);
  let passed = true;
  try {
    execFileSync("node", ["scripts/check-inline-styles.mjs", file], { stdio: "pipe" });
  } catch {
    passed = false;
  }
  check(`inline-style check ${shouldPass ? "passes" : "fails"} on ${name}`, passed === shouldPass);
}

if (failures > 0) {
  console.error(`${failures} check test(s) failed`);
  process.exit(1);
}
console.log("All style check tests passed");
