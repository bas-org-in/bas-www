#!/usr/bin/env bash
# Builds the deploy tree with scripts/prepare-deploy.sh, adds the lightbox
# files of the bas-gallery-publisher plugin from the bas-site-ops checkout
# beside this repository, and serves the tree on http://127.0.0.1:PORT/.
#
# Usage: tests/serve-local.sh DEPLOY_ROOT [PORT]
#
# BAS_PLUGIN_SOURCE names another plugin folder, for example in a worktree.
# BAS_VENDOR_SOURCE is passed to prepare-deploy.sh. The Python server does
# not run server-side includes.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
deploy_root="$1"
port="${2:-8765}"
plugin_src="${BAS_PLUGIN_SOURCE:-$repo_root/../bas-site-ops/wordpress/plugins/bas-gallery-publisher}"
plugin_dest="$deploy_root/wp/wp-content/plugins/bas-gallery-publisher"

"$repo_root/scripts/prepare-deploy.sh" "$deploy_root"
mkdir -p "$plugin_dest/assets"
cp "$plugin_src/lightbox.js" "$plugin_src/article-lightbox.js" "$plugin_dest/"
cp "$plugin_src/assets/bas-lightbox.css" "$plugin_dest/assets/"

exec python3 -m http.server "$port" --bind 127.0.0.1 --directory "$deploy_root"
