FROM docker.io/library/python@sha256:023f26fe8438a9622a4cc67665b54999850e00868a32d9b0b6fa3340f249df42 AS builder
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl git g++ libcurl4-nss-dev libffi-dev libfreetype-dev libimagequant-dev libjpeg62-turbo-dev libopenjp2-7-dev libraqm-dev libtiff-dev libwebp-dev libxml2-dev libxslt1-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/* \
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
        g/glib2.0/libglib2.0-0_2.74.6-1 \
        g/glib2.0/libglib2.0-bin_2.74.6-1 \
        g/glib2.0/libglib2.0-dev_2.74.6-1 \
        g/glib2.0/libglib2.0-dev-bin_2.74.6-1 \
        g/glibc/libc6_2.36-8 \
        g/glibc/libc-bin_2.36-8 \
        g/glibc/libc6-dev_2.36-8 \
        g/glibc/libc-dev-bin_2.36-8 \
        h/highway/libhwy1_1.0.3-3 \
        h/highway/libhwy-dev_1.0.3-3 \
        j/jansson/libjansson4_2.14-2 \
        j/jpeg-xl/libjxl0.7_0.7.0-10 \
        j/jpeg-xl/libjxl-dev_0.7.0-10 \
        l/lcms2/liblcms2-2_2.14-2 \
        l/lcms2/liblcms2-dev_2.14-2 \
        r/rpcsvc-proto/rpcsvc-proto_1.4.3-1 \
        libf/libffi/libffi8_3.4.4-1 \
        libz/libzstd/libzstd1_1.5.4+dfsg2-3 \
    ; \
    do \
        curl -sSfo $(echo $pkg | cut -d / -f 3)_amd64.deb https://snapshot.debian.org/archive/debian/20230312T152223Z/pool/main/${pkg}_amd64.deb \
    ; \
    done \
 && dpkg --auto-deconfigure -i *.deb \
 && apt-get check \
 && rm -f *.deb \
 && curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain nightly-2023-04-01 --profile minimal
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYCURL_SSL_LIBRARY=nss \
    PIP_NO_CACHE_DIR=1
# TODO: merge this into one (https://github.com/openshift/imagebuilder/pull/210 fixes the bug)
ARG AIOHTTP_NO_EXTENSIONS=1
ARG FROZENLIST_NO_EXTENSIONS=1
ARG YARL_NO_EXTENSIONS=1
COPY requirements.txt .
RUN set -eux \
 && . $HOME/.cargo/env \
 && python -m venv venv \
 && /venv/bin/pip install --no-deps wheel==0.40.0 \
 && /venv/bin/pip install --no-deps https://github.com/cython/cython/archive/dacb26cec739a2afa2ba9d305f05504168612bf8.tar.gz \
 && /venv/bin/pip install --no-deps funcparserlib==1.0.1 \
 && /venv/bin/pip install --no-deps --ignore-requires-python hy==0.26.0 \
 && /venv/bin/pip install --no-deps --no-build-isolation hyrule==0.3.0 \
 && /venv/bin/pip install --no-deps --no-build-isolation numpy==1.24.2 \
 && /venv/bin/pip install --no-deps --no-build-isolation UltraDict==0.0.6 \
 && /venv/bin/pip install --no-deps git+https://github.com/oconnor663/blake3-py.git@0.3.3#subdirectory=c_impl \
 && /venv/bin/pip install --no-deps --no-build-isolation https://github.com/roy-ht/editdistance/archive/v0.6.2.tar.gz \
 && /venv/bin/pip install --no-deps https://github.com/lxml/lxml/archive/11b33a83ad689bd16bd0a98c14cda51a90572b73.tar.gz \
 && CFLAGS="-fpermissive" /venv/bin/pip install --no-deps --no-build-isolation https://github.com/olokelo/jxlpy/archive/eebe73706b2c10153aa40d039e5e02c45a8168a4.tar.gz \
 && sed -E "/(blake3|lxml|uvloop)/d" requirements.txt > requirements2.txt \
 && /venv/bin/pip install -r requirements2.txt \
 && /venv/bin/pip uninstall -y wheel Cython
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM docker.io/library/python@sha256:023f26fe8438a9622a4cc67665b54999850e00868a32d9b0b6fa3340f249df42
RUN set -eux \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl libcurl3-nss libfreetype6 libimagequant0 libjpeg62-turbo libopenjp2-7 libwebp6 libwebpdemux2 libwebpmux3 libraqm0 libtiff5 nss-plugin-pem \
 && rm -rf /var/lib/apt/lists/* \
 && for pkg in \
        g/gcc-12/gcc-12-base_12.2.0-14 \
        g/gcc-12/libstdc++6_12.2.0-14 \
        g/glibc/libc-bin_2.36-8 \
        g/glibc/libc6_2.36-8 \
        h/highway/libhwy1_1.0.3-3 \
        l/lcms2/liblcms2-2_2.14-2 \
        j/jpeg-xl/libjxl0.7_0.7.0-10 \
    ; \
    do \
        curl -sSfo $(echo $pkg | cut -d / -f 3)_amd64.deb https://snapshot.debian.org/archive/debian/20230312T152223Z/pool/main/${pkg}_amd64.deb \
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
 && rm -rf uwufetch*
COPY --from=builder /venv /venv
RUN mkdir /data
WORKDIR /data
VOLUME /data
EXPOSE 8888
ENV DISABLE_UVLOOP=1
CMD ["/venv/bin/an-website", "--port", "8888"]
