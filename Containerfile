ARG BASE=docker.io/library/python:3.12.0b1-slim

FROM $BASE AS builder
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends automake curl git g++ libcurl4-gnutls-dev libffi-dev libfreetype-dev libgnutls28-dev libimagequant-dev libjpeg62-turbo-dev libopenjp2-7-dev libraqm-dev libtiff-dev libtool libwebp-dev libxml2-dev libxslt1-dev make zlib1g-dev \
 && rm -fr /var/lib/apt/lists/* \
 && for pkg in \
        b/binutils/binutils_2.40-2 \
        b/binutils/binutils-common_2.40-2 \
        b/binutils/binutils-x86-64-linux-gnu_2.40-2 \
        b/binutils/libbinutils_2.40-2 \
        b/binutils/libctf0_2.40-2 \
        b/binutils/libctf-nobfd0_2.40-2 \
        b/binutils/libgprofng0_2.40-2 \
        g/gcc-12/gcc-12-base_12.2.0-14 \
        g/gcc-12/libgcc-s1_12.2.0-14 \
        g/gcc-12/libstdc++6_12.2.0-14 \
        g/glib2.0/libglib2.0-0_2.74.6-2 \
        g/glib2.0/libglib2.0-bin_2.74.6-2 \
        g/glib2.0/libglib2.0-dev_2.74.6-2 \
        g/glib2.0/libglib2.0-dev-bin_2.74.6-2 \
        g/glibc/libc6_2.36-9 \
        g/glibc/libc-bin_2.36-9 \
        g/glibc/libc6-dev_2.36-9 \
        g/glibc/libc-dev-bin_2.36-9 \
        h/highway/libhwy1_1.0.3-3 \
        h/highway/libhwy-dev_1.0.3-3 \
        j/jansson/libjansson4_2.14-2 \
        j/jpeg-xl/libjxl0.7_0.7.0-10 \
        j/jpeg-xl/libjxl-dev_0.7.0-10 \
        l/lcms2/liblcms2-2_2.14-2 \
        l/lcms2/liblcms2-dev_2.14-2 \
        r/rpcsvc-proto/rpcsvc-proto_1.4.3-1 \
        libf/libffi/libffi8_3.4.4-1 \
        libz/libzstd/libzstd1_1.5.4+dfsg2-5 \
    ; \
    do \
        curl --retry 5 -sSfo $(echo $pkg | cut -d / -f 3)_amd64.deb https://snapshot.debian.org/archive/debian/20230501T024743Z/pool/main/${pkg}_amd64.deb \
    ; \
    done \
 && dpkg --auto-deconfigure -i *.deb \
 && apt-get check \
 && rm -f *.deb \
 && curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain beta-2023-05-27 --profile minimal
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYCURL_SSL_LIBRARY=gnutls \
    PIP_NO_CACHE_DIR=1 \
    RUSTC_BOOTSTRAP=1
ARG AIOHTTP_NO_EXTENSIONS=1 \
    FROZENLIST_NO_EXTENSIONS=1
COPY requirements.txt .
RUN set -eux \
 && . $HOME/.cargo/env \
 && python -m venv venv \
 && /venv/bin/pip install --no-deps git+https://github.com/MagicStack/uvloop.git@v0.17.0 \
 && /venv/bin/pip install --no-deps https://codeload.github.com/roy-ht/editdistance/tar.gz/v0.6.2 \
 && /venv/bin/pip install --no-deps setuptools wheel Cython \
 && /venv/bin/pip install --no-deps https://codeload.github.com/lxml/lxml/tar.gz/0268b8eb3287655303869e7b4e617ff0734fdfc4 \
 && /venv/bin/pip uninstall -y setuptools wheel Cython \
 && CFLAGS="-fpermissive" /venv/bin/pip install --no-deps https://codeload.github.com/olokelo/jxlpy/tar.gz/eebe73706b2c10153aa40d039e5e02c45a8168a4 \
 && /venv/bin/pip install --no-deps git+https://github.com/oconnor663/blake3-py.git@0.3.3#subdirectory=c_impl \
 && /venv/bin/pip install --no-deps git+https://github.com/pypy/pyrepl.git@ca192a80b76700118b9bfd261a3d098b92ccfc31 \
 && sed -Ei "/(blake3|lxml)/d" requirements.txt \
 && /venv/bin/pip install -r requirements.txt \
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM $BASE
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl libcurl3-gnutls libfreetype6 libimagequant0 libjpeg62-turbo libopenjp2-7 libraqm0 libtiff5 libwebp6 libwebpdemux2 libwebpmux3 libxml2 libxslt1.1 \
 && rm -fr /var/lib/apt/lists/* \
 && for pkg in \
        g/gcc-12/gcc-12-base_12.2.0-14 \
        g/gcc-12/libstdc++6_12.2.0-14 \
        g/glibc/libc-bin_2.36-9 \
        g/glibc/libc6_2.36-9 \
        h/highway/libhwy1_1.0.3-3 \
        j/jpeg-xl/libjxl0.7_0.7.0-10 \
        l/lcms2/liblcms2-2_2.14-2 \
    ; \
    do \
        curl -sSfo $(echo $pkg | cut -d / -f 3)_amd64.deb https://snapshot.debian.org/archive/debian/20230501T024743Z/pool/main/${pkg}_amd64.deb \
    ; \
    done \
 && dpkg --auto-deconfigure -i *.deb \
 && apt-get check \
 && rm -f *.deb \
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
      org.opencontainers.image.description="podman run --detach --name an-website --network slirp4netns:port_handler=slirp4netns --publish 8888:8888 --pull newer --volume .:/data:z IMAGE" \
      org.opencontainers.image.base.digest="$BASE_DIGEST" \
      org.opencontainers.image.base.name="$BASE_NAME"
