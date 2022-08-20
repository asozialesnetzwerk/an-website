#!/bin/sh
set -eu

pnpm install -q
pnpm eslint --report-unused-disable-directives an_website
