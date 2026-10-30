# BAS Main Website

This repository is part of the BAS website workspace. BAS members set it
up with `docs/workspace.md` in the repository `bas-org-in/bas-site-ops`.

Curated static source for the main Bangalore Astronomical Society website,
served at `https://bas.org.in/`.

See `import.md` for source provenance notes.

## Deployment

The main site deploys through a manual GitHub Actions workflow. See
[`docs/deployment.md`](docs/deployment.md).

## Styles

All design values (colours, type sizes, spacing, radii, weights, shadows
and control sizes) are tokens in `public/assets/css/tokens.css`.
`public/assets/css/bas-site.css` and every other stylesheet use them only
through `var(--bas-...)`. `bas-site.css` imports `tokens.css`, so a page
that links only `bas-site.css` still gets the tokens. Pages in this repo
link `tokens.css` first. The BAS WordPress theme and gallery plugin also
load `https://bas.org.in/assets/css/tokens.css`, so rename or remove a
token only together with them.

To add a value, add a token to `tokens.css` first, with a comment that
gives its role, then use the token.

## Checks

Checks run before each commit, as pre-commit hooks, and in CI on each push
and pull request (`.github/workflows/checks.yml`). They find mistakes before
a change reaches the live site:

- File hygiene: large files, merge conflict markers, invalid JSON and YAML,
  trailing spaces and missing final newlines.
- Secrets: private keys and other credentials (gitleaks).
- Markdown (markdownlint), JavaScript (ESLint), Python (Ruff), shell
  scripts (shellcheck) and GitHub Actions workflows (actionlint).
- Styles: stylelint rejects raw colours and raw font sizes, weights, radii,
  shadows and spacing outside `tokens.css`. A second check rejects `<style>`
  blocks and `style=` attributes in HTML, include and PHP files.

The checks skip the vendored Bootstrap and Font Awesome folders.

You need [Node.js](https://nodejs.org/) 22 and
[uv](https://docs.astral.sh/uv/getting-started/installation/).

Install the linters once, from the repository root:

```sh
npm ci
```

Install the pre-commit hook once, so the checks run on each `git commit`:

```sh
uvx pre-commit@4.7.0 install
```

Run all checks on all files:

```sh
uvx pre-commit@4.7.0 run --all-files
```

Run the tests of the style checks:

```sh
npm test
```

Run the browser test of the home page photo lightbox (AT-39 to AT-42 in
`docs/style-system-acceptance-tests.md` of `bas-site-ops`). It needs the
page on a real host name, because imgur and Google Photos refuse some
photos to a local address. Upload `public/index.html` to staging as
`home-lightbox-test.html` (`ops/staging.md` in `bas-site-ops`), then run:

```sh
BAS_TEST_HTTP_USER=... BAS_TEST_HTTP_PASSWORD=... \
  uv run --no-project --with playwright==1.55.0 python -I tests/home-photo-lightbox.py \
  https://staging.bas.org.in/home-lightbox-test.html <article page with images> <output folder>
```

`BAS_TEST_CHROME` names another browser, and `BAS_TEST_CHROME_ARGS` adds
browser flags, for example
`--host-resolver-rules="MAP staging.bas.org.in <address>"` while a local
DNS cache is out of date.

`tests/serve-local.sh` serves a local copy for quick checks; there, AT-42
fails for the photos that imgur and Google Photos refuse.

Run the browser test of the home page welcome banner (AT-47) against the
home page, for example on staging:

```sh
BAS_TEST_HTTP_USER=... BAS_TEST_HTTP_PASSWORD=... \
  uv run --no-project --with playwright==1.55.0 python -I tests/home-banner.py \
  https://staging.bas.org.in/
```

Run the browser test of the home page Events section (AT-51) the same
way. It reads the expected events from the site's events API:

```sh
BAS_TEST_HTTP_USER=... BAS_TEST_HTTP_PASSWORD=... \
  uv run --no-project --with playwright==1.55.0 python -I tests/home-events.py \
  https://staging.bas.org.in/
```

Some hooks fix files in place, such as trailing spaces. When a hook changes
a file, review the change, stage it and commit again. Fix other findings in
the code.
