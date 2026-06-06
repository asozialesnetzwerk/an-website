# syntax=docker.io/docker/dockerfile:1.24
# check=error=true;experimental=InvalidDefinitionDescription

ARG VARIANT=slim-trixie
ARG BASE=docker.io/library/python:3.14-$VARIANT

FROM $BASE AS builder
ARG VARIANT
RUN <<EOF
    set -eux

    if [ "${VARIANT}" = "alpine" ]
    then
        apk add --no-cache curl curl-dev g++ git libcurl make
    else
        apt-get update
        apt-get install -y --no-install-recommends curl g++ git libcurl4-gnutls-dev make
    fi

    curl -sSfLo uwufetch.tar.gz https://codeload.github.com/ad-oliviero/uwufetch/tar.gz/f3d4503e72fa5b7dff466e527453cfbf2c95cc01
    tar xvf uwufetch.tar.gz
    cd uwufetch-*
    make release
    mv uwufetch_-linux /built-uwufetch
    cd ..
    rm -fr uwufetch*
    mv /built-uwufetch /uwufetch

    if [ "${VARIANT}" = "alpine" ]
    then
        apk del -r curl make
    else
        apt-get purge -y --autoremove curl make
        rm -fr /var/lib/apt/lists/*
    fi
EOF

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_NO_CACHE_DIR=1
COPY pip-requirements.txt .
RUN <<EOF
    set -eux
    python -m venv venv
    /venv/bin/pip install pip==25.2.* Cython==3.* setuptools==68.* wheel==0.45.*
    /venv/bin/pip install --no-build-isolation https://codeload.github.com/ronny-rentner/UltraDict/tar.gz/9f88a2f73e6b7faadb591971c6a17b360ebbc3bf
    /venv/bin/pip uninstall -y Cython setuptools wheel
    /venv/bin/pip install -U pip
    /venv/bin/pip install git+https://github.com/pypy/pyrepl.git@502bcf766e22b7d3898ed318f4a02d575804eb6f
    if [ ! "${VARIANT}" = "alpine" ]
    then
        export PYCURL_SSL_LIBRARY=gnutls
    fi
    if python3 -c '__import__("sys").exit("ripemd160" not in __import__("hashlib").algorithms_available)'
    then
        # ripemd160 is available, no need for pycryptodome
        sed -ri s/pycryptodome==.+\$// pip-requirements.txt
    fi
    /venv/bin/pip install --no-deps --no-binary pycurl -r pip-requirements.txt
EOF
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM $BASE
ARG VARIANT
RUN --mount=type=bind,from=builder,source=/uwufetch,target=/uwufetch <<EOF
    set -eux
    if [ "${VARIANT}" = "alpine" ]
    then
        apk add --no-cache bash libcurl
    else
        apt-get update
        apt-get install -y --no-install-recommends libcurl3t64-gnutls
        rm -fr /var/lib/apt/lists/*
    fi
    cd /uwufetch
    ./install.sh
    cd -
    mkdir /data
EOF

COPY --from=builder /venv /venv
WORKDIR /data
VOLUME /data
EXPOSE 8888
ENTRYPOINT ["/venv/bin/an-website"]
CMD ["--port=8888", "--unix-socket-path=/data"]
