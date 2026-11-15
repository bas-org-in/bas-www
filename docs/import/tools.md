# bas-tools import notes

Base source: `website-source/tools/`

Imported from source:

- `index.html`
- `dss.html`
- `calclst.js`

Imported from live mirror:

- `logbooks/` from `mirrors/tools.bas.org.in/logbooks/`
- `ngc_search.htm` from `mirrors/tools.bas.org.in/ngc_search.htm`

Why mirror content was needed:

`website-source/tools/logbooks` and `website-source/tools/ngc_search.htm` were
broken symlinks to `/home/akarsh/public_html/...` in the local checkout.

Excluded:

- `logbooks/bootstrap/`, which is a third-party Bootstrap snapshot and is
  tracked under `curated/third-party/`.

Known issue:

The live `dss.php` link returned 404 during the crawl. The available static
source is `dss.html` plus `calclst.js`.
