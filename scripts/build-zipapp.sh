#!/bin/sh

set -eu

if [ -z "${VIRTUAL_ENV:-}" ] ; then
  echo 'Will not run outside of a venv.' >&2
  exit 1
fi

PYVERSION="$(python3 -c 'import sys;print(sys.implementation.name, end="-");print(*sys.version_info[:2], sep=".")')"
PLATFORM="$(python3 -c 'import sys;print(sys.platform)')"
ARCH="$(uname -m)"
rmdir "build/bdist.linux-${ARCH}" || true

set -x

pip3 install -r pip-requirements.txt >&2

VERSION="$(python3 -m an_website --version 2> /dev/null)"

pip install -U zipapps -c pip-constraints.txt >&2

# shellcheck disable=SC2016
python3 -m zipapps \
  -u 'AUTO,pillow,_geoip_geolite2,UltraDict' \
  -p '/usr/bin/env python3' \
  -o 'build/an_website.pyz' \
  -up '$HOME/.cache/an-website/zipapps' \
  --clear-zipapps-cache \
  --rm-patterns '**/__pycache__' \
  -m 'an_website.__main__:main' \
  -r 'pip-requirements.txt' . >&2

mkdir -p dist

RESULT_FILE="./dist/an-website-${VERSION}-${PYVERSION}-${ARCH}-${PLATFORM}.pyz"

mv build/an_website.pyz "${RESULT_FILE}"

echo "${RESULT_FILE}"
