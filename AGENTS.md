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
  canonical URL. Maintain historic archive entries in
  `public/sitemap-historic.xml`, preserving their existing `.htm` or `.html`
  extensions and exact filename casing. Do not make Historic URLs
  extensionless or add redirects that remove those extensions. The Historic
  sitemap is intentionally excluded from `public/robots.txt`; do not add it
  there.
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
