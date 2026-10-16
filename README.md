# BAS Main Website

Curated static source for the main Bangalore Astronomical Society website,
served at `https://bas.org.in/`.

This repo is part of the BAS website migration workspace. See `import.md` for
source provenance notes.

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

Stylelint rejects raw colours and raw font sizes, weights, radii, shadows
and spacing outside `tokens.css`. A second check rejects `<style>` blocks
and `style=` attributes in HTML, include and PHP files. CI runs both on
each push and pull request (`.github/workflows/checks.yml`).

Install the linters once:

```sh
npm ci
```

Run the checks:

```sh
npm run lint
```

Run the tests of the checks:

```sh
npm test
```

The same checks run as pre-commit hooks. Install the hook once:

```sh
uvx pre-commit@4.7.0 install
```

