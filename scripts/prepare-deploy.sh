#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 DEPLOY_ROOT" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
deploy_root="$1"
include_large_pdfs="${BAS_INCLUDE_LARGE_PDFS:-${BAS_INCLUDE_PDFS:-0}}"
install_vendor="${BAS_INSTALL_VENDOR:-1}"
vendor_source="${BAS_VENDOR_SOURCE:-}"
node_modules_root="${BAS_NODE_MODULES:-$repo_root/node_modules}"

case "$include_large_pdfs" in
  0|1) ;;
  *)
    echo "BAS_INCLUDE_LARGE_PDFS must be 0 or 1" >&2
    exit 2
    ;;
esac

case "$install_vendor" in
  0|1) ;;
  *)
    echo "BAS_INSTALL_VENDOR must be 0 or 1" >&2
    exit 2
    ;;
esac

if [ -e "$deploy_root" ]; then
  chmod -R u+w "$deploy_root" 2>/dev/null || true
  rm -rf "$deploy_root"
fi
mkdir -p "$deploy_root"
rsync -a "$repo_root/public/" "$deploy_root/"

if [ "$include_large_pdfs" = "0" ]; then
  rm -f \
    "$deploy_root/files/BASWinterAdvanced.pdf" \
    "$deploy_root/files/BASWinterBeginner.pdf" \
    "$deploy_root/files/BASWinterChallenge.pdf"
fi

copy_dir() {
  local src="$1"
  local dest="$2"

  if [ ! -d "$src" ]; then
    echo "vendor directory not found: $src" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$dest")"
  rsync -a --delete "$src/" "$dest/"
}

if [ "$install_vendor" = "1" ]; then
  if [ -n "$vendor_source" ]; then
    copy_dir "$vendor_source/vendor-public/bootstrap-3" "$deploy_root/bootstrap"
    copy_dir "$vendor_source/vendor-public/font-awesome-4.7.0" "$deploy_root/font-awesome-4.7.0"
  else
    copy_dir "$node_modules_root/bootstrap/dist" "$deploy_root/bootstrap"
    mkdir -p "$deploy_root/font-awesome-4.7.0"
    copy_dir "$node_modules_root/font-awesome/css" "$deploy_root/font-awesome-4.7.0/css"
    copy_dir "$node_modules_root/font-awesome/fonts" "$deploy_root/font-awesome-4.7.0/fonts"
  fi

  test -f "$deploy_root/bootstrap/css/bootstrap.min.css"
  test -f "$deploy_root/bootstrap/js/bootstrap.min.js"
  test -f "$deploy_root/font-awesome-4.7.0/css/font-awesome.min.css"
fi

test -f "$deploy_root/index.html"
