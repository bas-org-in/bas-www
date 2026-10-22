# Agent Notes

This repository is part of the BAS website workspace. BAS members set it
up with `docs/workspace.md` in the repository `bas-org-in/bas-site-ops`.

This repository holds the static source of the former `pages.bas.org.in`
site, served at `https://bas.org.in/pages/`. The files are in `public/`.
`README.md` describes the repository, and `import.md` records where the
files came from.

- Keep the files as static source. Do not add a build step.
- Do not commit third-party libraries. The OpenSans fonts and Respond.js
  (`public/assets/fonts/`, `public/assets/js/respond.js`) are ignored by git.
  The deploy installs them with `third-party/scripts/install-vendor.sh` of
  `bas-site-ops`.
- Do not commit credentials, hosting account notes or private data.
- The deploy and the URL map of the whole site are in `bas-site-ops`:
  `ops/deployment.md` and `docs/url-map.md`.

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
