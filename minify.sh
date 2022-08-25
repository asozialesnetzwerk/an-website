#!/bin/sh
set -eu

if [ "${1:-}" = "clean" ]; then
  rm -rf an_website/static/css
  rm -rf an_website/static/js
fi

find style \
  -type f -name "*.css" -exec \
    deno task --quiet esbuild \
      --outbase=style --outdir=an_website/static/css \
      --log-level=warning --charset=utf8 --minify {} +

find an_website \
  -type f -name "*.ts" -exec \
    deno task --quiet esbuild \
      --outbase=an_website --outdir=an_website/static/js \
      --log-level=warning --log-override:unsupported-regexp=error \
      --charset=utf8 --target=es2020 --minify --sourcemap {} +
