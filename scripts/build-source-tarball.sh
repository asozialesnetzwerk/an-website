#!/bin/sh

set -xeu
# shellcheck disable=SC3040
set -o pipefail

# create temp dir
TMP_DIR="$(mktemp -d)"

# create venv
python3 -m venv "${TMP_DIR}/venv"
pip="${TMP_DIR}/venv/bin/pip"

# run setup.py to generate files
"${pip}" install --no-deps .

# write version to file
"${pip}" show an_website | grep -P '^Version: ' | cut '-d ' -f2 > VERSIONS.TXT

# clean-up venv
rm -fr "${TMP_DIR}/venv"
# delete empty temp dir
rmdir "${TMP_DIR}"

# create tar ball
git -c tar.umask=0022 archive \
  --prefix an_website/static/ --add-file an_website/static/commits.txt --prefix '' \
  --add-file REVISION.TXT \
  --add-file TIMESTMP.TXT \
  --add-file VERSIONS.TXT \
  -o an-website.tar \
  HEAD

# compress tar ball
pigz -m -11 an-website.tar
