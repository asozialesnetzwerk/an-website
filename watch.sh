#!/bin/sh
set -eu

TARGET=es$(python -c "from datetime import datetime; print((now := datetime.utcnow()).year - (2 + (now.month < 7)))")

find an_website \
  -type f -name "*.ts" -exec \
    deno task --quiet esbuild \
      --outbase=an_website --outdir=an_website/static/js \
      --log-level=warning --log-override:unsupported-regexp=error \
      --charset=utf8 --target="${TARGET}" --minify --sourcemap --watch {} +
