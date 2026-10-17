import js from "@eslint/js";
import globals from "globals";

export default [
  {
    // Vendored third-party assets.
    ignores: ["public/bootstrap/**", "public/font-awesome-4.7.0/**", "node_modules/**"],
  },
  js.configs.recommended,
  {
    // Scripts that the site pages load in the browser. They are written as
    // ES5, so ESLint parses them as ES5. An ES5 catch clause must name its
    // error; the "ignored" prefix marks a catch that drops the error on
    // purpose, and other unused catch bindings are still reported.
    files: ["public/**/*.js"],
    languageOptions: { ecmaVersion: 5, sourceType: "script", globals: globals.browser },
    rules: {
      "no-unused-vars": ["error", { caughtErrorsIgnorePattern: "^ignored" }],
    },
  },
  {
    // Node check scripts.
    files: ["scripts/**/*.mjs", "eslint.config.mjs"],
    languageOptions: { sourceType: "module", globals: globals.node },
  },
];
