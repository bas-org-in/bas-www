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
