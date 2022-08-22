#!/bin/sh
set -eu

pnpm install -q

FAILED=0

echo tsc:
pnpm tsc || FAILED=$(( 2 | FAILED ))

echo ESLint:
pnpm eslint --report-unused-disable-directives an_website || FAILED=$(( 4 | FAILED ))

exit "${FAILED}"
