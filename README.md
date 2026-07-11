# BAS Main Website

Curated static source for the main Bangalore Astronomical Society website,
served at `https://bas.org.in/`.

This repo is part of the BAS website migration workspace. See `IMPORT.md` for
source provenance notes.

## GitHub Actions deploy

The `Deploy BAS main site to BigRock` workflow deploys `public/` to the BigRock
`public_html` tree over SSH. It is manual-only and defaults to an rsync dry run.

Required organization secrets in `bas-org-in`:

- `BAS_BIGROCK_HOST`
- `BAS_BIGROCK_USER`
- `BAS_BIGROCK_REMOTE_PATH`
- `BAS_BIGROCK_SSH_KEY`

The workflow preserves cPanel-managed paths such as `.well-known/`, `cgi-bin/`,
and `gallery/`. PDF uploads are optional and disabled by default because the
large winter PDFs are already managed separately.
