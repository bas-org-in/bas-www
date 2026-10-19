# Agent Notes

This repository is part of the BAS website workspace. BAS members set it
up with `docs/workspace.md` in the repository `bas-org-in/bas-site-ops`.

This repository holds the static source of the former `tools.bas.org.in`
site, served at `https://bas.org.in/tools/`. The files are in `public/`.
`README.md` describes the repository, and `import.md` records where the
files came from.

- Keep the files as static source. Do not add a build step.
- Do not commit third-party libraries. The Bootstrap 2 files of the logbooks
  (`public/logbooks/bootstrap/`) are ignored by git. The deploy installs them
  with `third-party/scripts/install-vendor.sh` of `bas-site-ops`.
- Do not commit credentials, hosting account notes or private data.
- The deploy and the URL map of the whole site are in `bas-site-ops`:
  `ops/deployment.md` and `docs/url-map.md`.
