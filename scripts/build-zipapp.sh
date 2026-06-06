#!/bin/sh

set -eu
# shellcheck disable=SC3040
set -o pipefail

if [ -z "${VIRTUAL_ENV:-}" ] ; then
  echo 'Will not run outside of a venv.' >&2
  exit 1
fi

export SOURCE_DATE_EPOCH=0

PYVERSION="$(python3 -c 'import sys;print(sys.implementation.name, end="-");print(*sys.version_info[:2], sep=".")')"
PLATFORM="$(python3 -c 'import sys;print(sys.platform)')"
ARCH="$(uname -m)"
rmdir "build/bdist.linux-${ARCH}" || true

set -x

pip3 install -U dulwich get_version setuptools -c pip-constraints.txt >&2

VERSION="$(./setup.py --version)"

pip3 install -U zipapps zopflipy time-machine -c pip-constraints.txt >&2

# shellcheck disable=SC2016
./scripts/zipapps_patched.py \
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
