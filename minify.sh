#!/bin/sh
set -eu

ESBUILD_VERSION=0.15.5
ESBUILD_URL=https://deno.land/x/esbuild@v${ESBUILD_VERSION}/mod.js

if [ "${1:-}" = "clean" ]; then
  rm -rf an_website/static/css
  rm -rf an_website/static/js
fi

find style \
  -type f -name "*.css" -exec \
    deno run -A "${ESBUILD_URL}" \
      --outbase=style --outdir=an_website/static/css \
      --log-level=warning --charset=utf8 --minify {} +

find an_website \
  -type f -name "*.ts" -exec \
    deno run -A "${ESBUILD_URL}" \
      --outbase=an_website --outdir=an_website/static/js \
      --log-level=warning --log-override:unsupported-regexp=error \
      --charset=utf8 --target=es2020 --minify --sourcemap {} +
