# Deployment

This repo deploys the main BAS static site to the BigRock cPanel document root.
The deploy is manual-only through GitHub Actions.

## Workflow

Use the `Deploy BAS main site to BigRock` workflow:

```text
.github/workflows/deploy-bigrock.yml
```

The workflow:

- prepares a temporary deploy tree from `public/`;
- installs Bootstrap 3.4.1 and Font Awesome 4.7.0 into the legacy root paths;
- connects to BigRock over SSH;
- syncs the prepared tree to the configured `public_html` path.

The workflow defaults to:

- `dry_run: true`
- `include_large_pdfs: false`
- `deploy_vendor: true`

Run the default dry run first. Review the rsync itemized changes in the Actions
log before rerunning with `dry_run: false`.

## Required Secrets

The workflow reads these organization secrets from `bas-org-in`:

```text
BAS_BIGROCK_HOST
BAS_BIGROCK_USER
BAS_BIGROCK_REMOTE_PATH
BAS_BIGROCK_SSH_KEY
```

`BAS_BIGROCK_REMOTE_PATH` must be `public_html` or an absolute path ending in
`public_html`. The workflow refuses other targets.

Do not commit real cPanel credentials, private keys, or secret values.

## Shared Styles

The deploy includes `assets/css/tokens.css` and `assets/css/bas-site.css`.
The WordPress theme and gallery plugin load both files from
`https://bas.org.in/assets/` at run time. Deploy a token rename together
with the WordPress code that uses it.

## Preserved Remote Paths

The sync does not use `rsync --delete`. It also excludes cPanel-managed paths:

```text
/.htaccess
/index.php
.well-known/
cgi-bin/
gallery/
wp/
```

This keeps certificate, CGI, and WordPress files outside the static site deploy.
`/.htaccess` and `/index.php` are the root `.htaccess` and the WordPress loader
in the document root; `bas-site-ops` keeps them (`docs/site-addresses.md`,
SA-21 and SA-22). `.htaccess` files in subfolders of `public/`, such as
`blogs/.htaccess`, are deployed. `wp/` is the WordPress core and admin install.
`gallery/` is excluded so that a deploy never writes there; `/gallery/` is a
WordPress page.

## Article Listing

`public/blogs/index.html` is the static article listing at
`https://bas.org.in/blogs/`. It reads the published articles from the
WordPress REST API at `/wp-json/`, with topic links and page links
(`bas-site-ops` `docs/article-addresses.md`, AA-20 to AA-34). Articles are
WordPress posts in the Articles category, with the address
`https://bas.org.in/blogs/<post name>/`.

`public/blogs/.htaccess` has no rewrite rules. The root `.htaccess` sends a
path that is not a file in `blogs/` to WordPress, which shows the article. The
file refuses `xmlrpc.php` and `.ht*` files.

Check after a deploy:

```sh
curl -sI https://bas.org.in/blogs/ | head -1
```

```sh
curl -sI https://bas.org.in/blogs/no-such-article/ | grep -i -E '^HTTP|^link'
```

```sh
curl -sI "https://bas.org.in/blogs/no-such-article/?author=1" | head -1
```

The first command prints `HTTP/2 200` (the static listing). The second prints
`HTTP/2 404` and a `link:` line that names `/wp-json/`, so the 404 page comes
from WordPress. The third prints `HTTP/2 403` (no author scans, SA-7).

After a change to `assets/css/bas-site.css` or `assets/js/bas-wp-posts.js`,
purge their addresses in the Cloudflare cache (`bas-site-ops`
`ops/deployment.md`).

## PDFs

Normal site PDFs, including the overview presentation and membership form, are
included in the default deploy. The large winter PDFs are excluded by default
because they are managed separately. Enable `include_large_pdfs` only when those
large files intentionally need to be refreshed from this repo.

## Local Deploy Tree Check

To validate the deploy assembly locally without contacting BigRock:

```sh
BAS_INCLUDE_LARGE_PDFS=0 scripts/prepare-deploy.sh /tmp/bas-www-deploy
test -f /tmp/bas-www-deploy/index.html
test -f /tmp/bas-www-deploy/blogs/.htaccess
test -f /tmp/bas-www-deploy/files/BAS_Overview.pdf
test -f /tmp/bas-www-deploy/bootstrap/css/bootstrap.min.css
test -f /tmp/bas-www-deploy/font-awesome-4.7.0/css/font-awesome.min.css
```

If using a local vendor snapshot instead of npm packages, set
`BAS_VENDOR_SOURCE` to a directory containing `vendor-public/`.
