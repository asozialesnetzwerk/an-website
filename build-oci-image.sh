#!/bin/sh
set -xeu

alias yq="podman run -i --rm --security-opt=no-new-privileges --cap-drop=all --network=none docker.io/mikefarah/yq:4"
alias oras="podman run -i --rm --network=host ghcr.io/oras-project/oras:v1.3.2"

VARIANT="${VARIANT:-slim-trixie}"
TAG="3.14-${VARIANT}"
TITLE="${TITLE:-an-website}"
IMAGE_NAME="${IMAGE_NAME:-an-website}"
GIT_REPOSITORY=https://github.com/asozialesnetzwerk/an-website

BASE_IMAGE="${BASE_IMAGE:-docker.io/library/python:${TAG}}"

BASE=$(oras resolve -dl "${BASE_IMAGE}")

DIGEST=$(echo "${BASE}" | cut -d @ -f 2)

VERSION=$(./setup.py --version)

REVISION=$(cat REVISION.TXT)

TIMESTAMP=$(python3 -c "from datetime import datetime; print(int(datetime.fromisoformat(\"$(cat TIMESTMP.TXT || true)\").timestamp()))")

buildah build \
  --network=host \
  --timestamp "${TIMESTAMP}" \
  --build-arg "BASE=${BASE}" \
  --build-arg "VARIANT=${VARIANT}" \
  --created-annotation \
  --annotation org.opencontainers.image.title="${TITLE}" \
  --annotation org.opencontainers.image.version="${VERSION}" \
  --annotation org.opencontainers.image.revision="${REVISION}" \
  --annotation org.opencontainers.image.licenses="AGPL-3.0-or-later" \
  --annotation org.opencontainers.image.authors="contact@asozial.org" \
  --annotation org.opencontainers.image.vendor="Das Asoziale Netzwerk" \
  --annotation org.opencontainers.image.source="${GIT_REPOSITORY}" \
  --annotation org.opencontainers.image.url="${GIT_REPOSITORY}/pkgs/container/${IMAGE_NAME}" \
  --annotation org.opencontainers.image.description="podman run --detach --name ${IMAGE_NAME} --network slirp4netns:port_handler=slirp4netns --publish 8888:8888 --volume .:/data:z IMAGE" \
  --annotation org.opencontainers.image.base.digest="${DIGEST}" \
  --annotation org.opencontainers.image.base.name="${BASE_IMAGE}" \
  "$@" .
