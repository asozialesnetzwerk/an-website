#!/bin/sh
set -eu

find an_website \
  -type f -name "*.ts" -exec \
    deno task --quiet esbuild \
      --outbase=an_website --outdir=an_website/static/js \
      --log-level=warning --log-override:unsupported-regexp=error \
      --charset=utf8 --target=es2020 --minify --sourcemap --watch {} +
