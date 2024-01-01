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

buildah build \
  --build-arg BASE="${BASE}" \
  --annotation org.opencontainers.image.authors="contact@asozial.org" \
  --annotation org.opencontainers.image.source="https://github.com/asozialesnetzwerk/an-website" \
  --annotation org.opencontainers.image.version="${VERSION}" \
  --annotation org.opencontainers.image.revision="${REVISION}" \
  --annotation org.opencontainers.image.vendor="Das Asoziale Netzwerk" \
  --annotation org.opencontainers.image.licenses="AGPL-3.0-or-later" \
  --annotation org.opencontainers.image.title="an-website" \
  --annotation org.opencontainers.image.description="podman run --detach --name an-website --network slirp4netns:port_handler=slirp4netns --publish 8888:8888 --volume .:/data:z IMAGE" \
  --annotation org.opencontainers.image.base.digest="${DIGEST}" \
  --annotation org.opencontainers.image.base.name="${NAME}" \
  "$@" .
