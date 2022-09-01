#!/bin/sh
set -eu

TARGET=es$(python3 -c "from datetime import datetime; print((now := datetime.utcnow()).year - (2 + (now.month < 7)))")

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
      --charset=utf8 --target="${TARGET}" --minify --sourcemap {} +
