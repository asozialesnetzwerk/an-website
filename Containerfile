# syntax=docker.io/docker/dockerfile:1.6
ARG BASE=docker.io/library/python:3.12-slim-bookworm

FROM $BASE AS builder
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends automake curl git g++ libcurl4-gnutls-dev libffi-dev libgnutls28-dev libtool libxml2-dev libxslt1-dev make zlib1g-dev \
 && rm -fr /var/lib/apt/lists/* \
 && curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain 1.70 --profile minimal
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYCURL_SSL_LIBRARY=gnutls \
    PIP_NO_CACHE_DIR=1 \
    RUSTC_BOOTSTRAP=1
COPY pip-requirements.txt .
RUN set -eux \
 && . $HOME/.cargo/env \
 && python -m venv venv \
 && /venv/bin/pip install setuptools==68.* wheel==0.42.* Cython==3.* \
 && /venv/bin/pip install https://codeload.github.com/lxml/lxml/tar.gz/762f62c5a1ab62ce37397aeeab2c27fdcc14ca66 \
 && CFLAGS="-DCYTHON_USE_PYLONG_INTERNALS=0" /venv/bin/pip install --no-build-isolation https://codeload.github.com/ronny-rentner/UltraDict/tar.gz/9f88a2f73e6b7faadb591971c6a17b360ebbc3bf \
 && /venv/bin/pip install git+https://github.com/oconnor663/blake3-py.git@0.3.3#subdirectory=c_impl \
 && /venv/bin/pip install git+https://github.com/pypy/pyrepl.git@ca192a80b76700118b9bfd261a3d098b92ccfc31 \
 && sed -Ei "/(blake3|lxml|orjson)/d" pip-requirements.txt \
 && /venv/bin/pip install -r pip-requirements.txt \
 && /venv/bin/pip uninstall -y setuptools wheel Cython
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM $BASE
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl libcurl3-gnutls libjxl0.7 libxml2 libxslt1.1 \
 && rm -fr /var/lib/apt/lists/* \
 && curl -sSfLo uwufetch_2.1-linux.tar.gz https://github.com/TheDarkBug/uwufetch/releases/download/2.1/uwufetch_2.1-linux.tar.gz \
 && tar xvf uwufetch_2.1-linux.tar.gz \
 && cd uwufetch_2.1-linux \
 && bash install.sh \
 && cd .. \
 && rm -fr uwufetch* \
 && mkdir /data
COPY --from=builder /venv /venv
WORKDIR /data
VOLUME /data
EXPOSE 8888
ENTRYPOINT ["/venv/bin/an-website"]
CMD ["--port=8888", "--unix-socket-path=/data"]
ARG BASE
ARG VERSION \
    REVISION \
    BASE_DIGEST \
    BASE_NAME=$BASE
LABEL org.opencontainers.image.authors="contact@asozial.org" \
      org.opencontainers.image.source="https://github.com/asozialesnetzwerk/an-website" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.revision="$REVISION" \
      org.opencontainers.image.vendor="Das Asoziale Netzwerk" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.title="an-website" \
      org.opencontainers.image.description="podman run --detach --name an-website --network slirp4netns:port_handler=slirp4netns --publish 8888:8888 --volume .:/data:z IMAGE" \
      org.opencontainers.image.base.digest="$BASE_DIGEST" \
      org.opencontainers.image.base.name="$BASE_NAME"
