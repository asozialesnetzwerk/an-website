#!/bin/sh
set -eu
# shellcheck disable=SC3040
set -o pipefail

pnpm install -q

FAILED=0

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
