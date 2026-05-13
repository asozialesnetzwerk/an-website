#!/bin/sh

set -eu

if [ -z "${1:-}" ] || [ "${#}" != '1' ]
then
  printf 'USAGE: %s {TAG}\n' "$0"
  printf 'e.g.:  %s %s\n' "$0" "$(date -u '+v%y.%m' || :)"
  exit 1
fi

# shellcheck disable=SC3040
set -o pipefail
set -x

TAG="${1}"
DIR="$(pwd)"

# create temp dir
TMP_DIR="$(mktemp -d)"

if [ -n "${DEBUG:-}" ]
then
  # shellcheck disable=SC1003
  TMP_DIR="${TMP_DIR}/$(printf ' \n \n ÄÖÜẞ \\')"
  mkdir -p "${TMP_DIR}"
fi

REPOSITORY="asozialesnetzwerk/an-website"
RELEASE_JSON="${TMP_DIR}/release-${TAG}.json"
wget -O "${RELEASE_JSON}" "https://api.github.com/repos/${REPOSITORY}/releases/tags/${TAG}"
SOURCE_TARBALL_URL="$(jq -r '.assets.[] | select(.name == "an-website.tar.gz") | .browser_download_url' < "${RELEASE_JSON}")"


# create venv
python3 -m venv "${TMP_DIR}/venv"
pip="${TMP_DIR}/venv/bin/pip"

# install build
"${pip}" install build
build="${TMP_DIR}/venv/bin/pyproject-build"

# build from source tarball
mkdir "${TMP_DIR}/source-tarball"
"${pip}" wheel --no-deps -w "${TMP_DIR}/source-tarball" "${SOURCE_TARBALL_URL}"
mkdir "${TMP_DIR}/source-tarball-build-sdist-temp"
cd "${TMP_DIR}/source-tarball-build-sdist-temp"
wget "${SOURCE_TARBALL_URL}"
tar xf "an-website.tar.gz"
"${build}" -so "${TMP_DIR}/source-tarball/" .
cd "${DIR}"

VERSION="$(cat "${TMP_DIR}/source-tarball-build-sdist-temp/VERSIONS.TXT")"

[ -n "${VERSION}" ]

# build from git
AN_WEBSITE_DIR="${TMP_DIR}/an-website"
if [ -d .git ]
then
  git clone --filter=tree:0 -b "${TAG}" . "${AN_WEBSITE_DIR}"
else
  git clone --filter=tree:0 -b "${TAG}" "https://github.com/${REPOSITORY}" "${AN_WEBSITE_DIR}"
fi
cd "${AN_WEBSITE_DIR}"
"${build}" .
cd "${DIR}"

# build/download from pypi
mkdir "${TMP_DIR}/pypi"
"${pip}" wheel    --no-deps -w "${TMP_DIR}/pypi" "an-website==${VERSION}"
"${pip}" download --no-binary an-website --no-deps -d "${TMP_DIR}/pypi" "an-website==${VERSION}"

# get files from github
mkdir "${TMP_DIR}/github"
cd "${TMP_DIR}/github"
WHEEL_FILENAME="an_website-${VERSION}-py3-none-any.whl"
WHEEL_URL="$(jq -r ".assets.[] | select(.name == \"${WHEEL_FILENAME}\") | .browser_download_url"  < "${RELEASE_JSON}")"
wget "${WHEEL_URL}"
WHEEL_DIGEST="$(jq -r ".assets.[] | select(.name == \"${WHEEL_FILENAME}\") | .digest" < "${RELEASE_JSON}")"
WHEEL_HASH="$(printf '%s' "${WHEEL_DIGEST}" | cut -d: -f2)"
WHEEL_HASH_ALG="$(printf '%s' "${WHEEL_DIGEST}" | cut -d: -f1)"
[ "${WHEEL_HASH_ALG}" = "sha256" ] && printf '%s' "${WHEEL_HASH} an_website-${VERSION}-py3-none-any.whl" | sha256sum -c --strict
SDIST_FILENAME="an_website-${VERSION}.tar.gz"
SDIST_URL="$(jq -r ".assets.[] | select(.name == \"${SDIST_FILENAME}\") | .browser_download_url" < "${RELEASE_JSON}")"
wget "${SDIST_URL}"
SDIST_DIGEST="$(jq -r ".assets.[] | select(.name == \"${SDIST_FILENAME}\") | .digest" < "${RELEASE_JSON}")"
SDIST_HASH="$(printf '%s' "${SDIST_DIGEST}" | cut -d: -f2)"
SDIST_HASH_ALG="$(printf '%s' "${SDIST_DIGEST}" | cut -d: -f1)"
[ "${SDIST_HASH_ALG}" = "sha256" ] && printf '%s' "${SDIST_HASH} ${SDIST_FILENAME}" | sha256sum -c --strict
cd "${DIR}"

# store lists of files
printf '%s\0' "${TMP_DIR}"/github/*.tar.gz "${TMP_DIR}"/pypi/*.tar.gz "${TMP_DIR}"/source-tarball/*.tar.gz "${AN_WEBSITE_DIR}"/dist/*.tar.gz > "${TMP_DIR}/ALL_SDISTS"
printf '%s\0' "${TMP_DIR}"/github/*.whl    "${TMP_DIR}"/pypi/*.whl    "${TMP_DIR}"/source-tarball/*.whl    "${AN_WEBSITE_DIR}"/dist/*.whl    > "${TMP_DIR}/ALL_WHEELS"

# check if files could be reproduced
SUCCESS=1
# shellcheck disable=SC2016
xargs -0n1 sh -c 'set -xeu && [ "$0  $1" = "$(sha256sum -z "$1")" ]' "${SDIST_HASH}" < "${TMP_DIR}/ALL_SDISTS" || SUCCESS=0
# shellcheck disable=SC2016
xargs -0n1 sh -c 'set -xeu && [ "$0  $1" = "$(sha256sum -z "$1")" ]' "${WHEEL_HASH}" < "${TMP_DIR}/ALL_WHEELS" || SUCCESS=0

# hash all files
xargs -0 sha256sum < "${TMP_DIR}/ALL_SDISTS"
xargs -0 sha256sum < "${TMP_DIR}/ALL_WHEELS"

# print failure
if [ "${SUCCESS}" -eq 0 ]
then
  set +x
  printf "Could not reproduce release.\n"
  printf "Mismatch could be caused by differences in the environment (e.g. zstandard version)\n"
  exit 1
fi

# delete temp dir on success only, on failure you may want to check what's wrong
rm -r "${TMP_DIR}"

set +x
printf "Successfully reproduced version %s\n" "${VERSION}"
