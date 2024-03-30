# syntax=docker.io/docker/dockerfile:1.6
ARG BASE=docker.io/library/python:3.12-slim-bookworm

FROM $BASE AS builder
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends automake curl git g++ libcurl4-gnutls-dev libffi-dev libgnutls28-dev libtool make zlib1g-dev \
 && rm -fr /var/lib/apt/lists/* \
 && curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain 1.75
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYCURL_SSL_LIBRARY=gnutls \
    PIP_NO_CACHE_DIR=1 \
    RUSTC_BOOTSTRAP=1
COPY pip-requirements.txt .
RUN set -eux \
 && . $HOME/.cargo/env \
 && python -m venv venv \
 && /venv/bin/pip install Cython==3.* setuptools==68.* wheel==0.42.* \
 && CFLAGS="-DCYTHON_USE_PYLONG_INTERNALS=0" /venv/bin/pip install --no-build-isolation https://codeload.github.com/ronny-rentner/UltraDict/tar.gz/9f88a2f73e6b7faadb591971c6a17b360ebbc3bf \
 && /venv/bin/pip install git+https://github.com/pypy/pyrepl.git@502bcf766e22b7d3898ed318f4a02d575804eb6f \
 && /venv/bin/pip install --no-binary pycurl -r pip-requirements.txt \
 && /venv/bin/pip uninstall -y Cython setuptools wheel
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM $BASE
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl libcurl3-gnutls libjxl0.7 \
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
