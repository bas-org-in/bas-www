# bas-www import notes

Base source: `website-source/`

Imported:

- `index.html`
- `style.css`
- `footer.inc`
- BAS-owned assets under `files/`

Excluded:

- `website-source/bootstrap/` and `website-source/font-awesome-4.7.0/`
  because they are third-party vendor assets.
- `website-source/tools/` because it is split into `repos/bas-tools`.
- archives: `bas-website.tar.gz`, `files/bas.org.in.tar.bz2`
- backups/probes/old code: `*~`, `*.bak`, `*.wtf`, `old/`, `Home`

Verification source:

- `mirrors/www.bas.org.in` matched this source as a public crawl subset, with
  only expected `wget --convert-links` differences in comparable files.
