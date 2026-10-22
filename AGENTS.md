# Agent Notes

This repository is part of the BAS website workspace. BAS members set it
up with `docs/workspace.md` in the repository `bas-org-in/bas-site-ops`.

This repository holds the static main site of the Bangalore Astronomical
Society, served at `https://bas.org.in/`. `README.md` describes the layout,
the checks and the deployment.

- Run `uvx pre-commit@4.7.0 run --all-files` before a commit, and fix
  findings in the code.
- Take every colour, size, spacing and radius from
  `public/assets/css/tokens.css`. Other stylesheets use only `var(--bas-...)`.
- Keep `public/sitemap.xml` in sync with every public static page and use its
  canonical URL. Maintain Historic archive entries in
  `public/sitemap-historic.xml` as extensionless canonical URLs, preserving
  the exact filename casing. Apache serves the existing `.htm` and `.html`
  files internally at those extensionless URLs and redirects extensionful
  requests to the canonical URLs. List the Historic sitemap directly in
  `public/robots.txt`; keep it separate from the root `sitemap.xml`.
- A directory index served slashless needs a `<base href>` with its
  slash-form directory path so relative links and assets keep working.
- `public/includes/global-nav.html` is the master BAS navigation fragment.
  Static pages include it with Apache SSI, and each repository has a local
  fragment copy so its pages work with the current repository layout. When
  changing navigation, update the master and all copies. Each page sets
  `BAS_NAV_CURRENT` to `home`, `tools`, `policy`, `historic`, `pages` or
  `blogs` immediately before its SSI include; preserve the correct value.
  Apache must have `mod_include` enabled and parse `.html` and `.htm` files
  with `IncludesNOEXEC`, as configured in
  `bas-site-ops/ops/static-index-routing.conf`. When the older repositories
  are consolidated into `bas-www`, their fragment copies can be retired.
- `public/includes/site-assets.html` is the master include for the shared BAS
  theme script and site styles. It loads `tokens.css` before `bas-site.css`.
  Static pages include each repository's local copy from the head. Update the
  master and all copies together; keep page-specific scripts and stylesheets
  outside this include.
- Deploy only through the guarded workflow in `docs/deployment.md`.

## Pull Requests

Every change goes through a pull request that a maintainer reviews and
merges. Follow `docs/pull-requests.md` in `bas-org-in/bas-site-ops`:

- Work on a branch named `<type>/<short-topic>`, never on `main`.
- Fill in every section of the pull request template.
- Before you open the pull request, review the change with
  `skills/bas-pr-review/SKILL.md` in `bas-site-ops`, and fix what it
  finds.
- Do not change workflows, `.htaccess` files or deploy scripts without a
  maintainer's agreement.
- Do not merge your own pull request.
