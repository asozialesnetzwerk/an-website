#!/bin/sh
set -eu

pnpm install -q

FAILED=0

if [ "${USE_BUN:-}" = "1" ]; then
  alias pnpm="bunx --bun"
fi

echo tsc:
pnpm tsc || FAILED=$(( 2 | FAILED ))
pnpm tsc -p an_website || FAILED=$(( 2 | FAILED ))

echo ESLint:
if [ "${1:-}" = "--fix" ]; then
  pnpm eslint --fix . || FAILED=$(( 4 | FAILED ))
else
  pnpm eslint . || FAILED=$(( 4 | FAILED ))
fi

exit "${FAILED}"
