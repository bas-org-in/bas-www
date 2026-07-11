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
- `include_pdfs: false`
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

## Preserved Remote Paths

The sync does not use `rsync --delete`. It also excludes cPanel-managed paths:

```text
.htaccess
.well-known/
cgi-bin/
gallery/
```

This keeps certificate, CGI, and WordPress gallery files outside the static site
deploy.

## PDFs

PDF uploads are disabled by default because the winter PDFs are large and are
managed separately. Enable `include_pdfs` only when the site PDFs intentionally
need to be refreshed from this repo.

## Local Deploy Tree Check

To validate the deploy assembly locally without contacting BigRock:

```sh
BAS_INCLUDE_PDFS=0 scripts/prepare-deploy.sh /tmp/bas-www-deploy
test -f /tmp/bas-www-deploy/index.html
test -f /tmp/bas-www-deploy/bootstrap/css/bootstrap.min.css
test -f /tmp/bas-www-deploy/font-awesome-4.7.0/css/font-awesome.min.css
```

If using a local vendor snapshot instead of npm packages, set
`BAS_VENDOR_SOURCE` to a directory containing `vendor-public/`.
