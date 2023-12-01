#!/bin/sh
set -eu

TAG=3.12-slim-bookworm
REPOSITORY=library/python
NAME=docker.io/${REPOSITORY}:${TAG}
REGISTRY=https://index.docker.io/v2
AUTH_REALM=https://auth.docker.io/token
AUTH_SERVICE=registry.docker.io
AUTH_SCOPE=repository:${REPOSITORY}:pull
AUTH_URL="${AUTH_REALM}?service=${AUTH_SERVICE}&scope=${AUTH_SCOPE}"
TOKEN=$(curl -sSf "${AUTH_URL}" | jq -er .token)
MANIFEST_URL=${REGISTRY}/${REPOSITORY}/manifests/${TAG}
HEADERS=$(curl -sSf --head --oauth2-bearer "${TOKEN}" -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" "${MANIFEST_URL}")
DIGEST=$(echo "${HEADERS}" | grep "digest" | cut -d " " -f 2 | git stripspace)
BASE=docker.io/${REPOSITORY}@${DIGEST}

VERSION=$(./setup.py --version)

REVISION=$(cat REVISION.txt)

echo "--build-arg BASE=${BASE} --build-arg BASE_DIGEST=${DIGEST} --build-arg BASE_NAME=${NAME} --build-arg REVISION=${REVISION} --build-arg VERSION=${VERSION}"
