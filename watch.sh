#!/bin/sh
set -eu

ESBUILD_VERSION=0.15.5
ESBUILD_URL=https://deno.land/x/esbuild@v${ESBUILD_VERSION}/mod.js

find an_website \
  -type f -name "*.ts" -exec \
    deno run -A "${ESBUILD_URL}" \
      --outbase=an_website --outdir=an_website/static/js \
      --log-level=warning --log-override:unsupported-regexp=error \
      --charset=utf8 --target=es2020 --minify --sourcemap --watch {} +
