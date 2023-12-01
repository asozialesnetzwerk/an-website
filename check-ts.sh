#!/bin/sh
set -eu

pnpm install -q

FAILED=0

echo tsc:
pnpm tsc -p an_website || FAILED=$(( 2 | FAILED ))

echo ESLint:
if [ "${1:-}" = "--fix" ]; then
  pnpm eslint --fix . || FAILED=$(( 4 | FAILED ))
else
  pnpm eslint . || FAILED=$(( 4 | FAILED ))
fi

exit "${FAILED}"
