#!/usr/bin/env node
// Fails when an HTML, include or PHP template has a <style> block or a
// style= attribute. Stylelint reads only stylesheets, so this check covers
// the templates. Styles belong in a stylesheet that uses design tokens.
//
// Usage: node scripts/check-inline-styles.mjs [--root DIR]... [FILE]...
// With no FILE, the script checks every template under each --root.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const EXTENSIONS = new Set([".html", ".htm", ".inc", ".php"]);
const PATTERNS = [
  { name: "<style> block", regex: /<style\b/i },
  { name: "style= attribute", regex: /[\s"']style\s*=/i },
];

function walk(dir, out) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name.startsWith(".")) {
      continue;
    }
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(path, out);
    } else if (EXTENSIONS.has(extname(entry.name).toLowerCase())) {
      out.push(path);
    }
  }
  return out;
}

const args = process.argv.slice(2);
const files = [];
for (let i = 0; i < args.length; i += 1) {
  if (args[i] === "--root") {
    i += 1;
    if (statSync(args[i], { throwIfNoEntry: false })?.isDirectory()) {
      walk(args[i], files);
    }
  } else if (EXTENSIONS.has(extname(args[i]).toLowerCase())) {
    files.push(args[i]);
  }
}

let problems = 0;
for (const file of files) {
  readFileSync(file, "utf8").split("\n").forEach((line, index) => {
    for (const { name, regex } of PATTERNS) {
      if (regex.test(line)) {
        problems += 1;
        console.error(`${file}:${index + 1}: ${name} is not allowed; use a class in a stylesheet`);
      }
    }
  });
}

if (problems > 0) {
  console.error(`${problems} inline style problem(s) in ${files.length} file(s)`);
  process.exit(1);
}
console.log(`No inline styles in ${files.length} template file(s)`);
