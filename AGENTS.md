# Agent Notes

This repository is part of the BAS website workspace. BAS members set it
up with `docs/workspace.md` in the repository `bas-org-in/bas-site-ops`.

This repository holds the static source of the former `historic.bas.org.in`
site, served at `https://bas.org.in/historic/`. The files are in `public/`.
`README.md` describes the repository, and `import.md` records where the
files came from.

- Keep the files as static source. Do not add a build step.
- Do not commit third-party libraries such as Bootstrap or Font Awesome.
- Do not commit credentials, hosting account notes or private data.
- The deploy and the URL map of the whole site are in `bas-site-ops`:
  `ops/deployment.md` and `docs/url-map.md`.

## Pull Requests

Every change goes through a pull request. The rules, including who
merges a pull request and when, are in `docs/pull-requests.md` of
`bas-org-in/bas-site-ops`. Review a change with
`skills/bas-pr-review/SKILL.md` of that repository.
