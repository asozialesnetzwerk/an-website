FROM docker.io/library/python:3.10-slim AS builder
RUN apt-get update \
 && apt-get install -y --no-install-recommends git g++ libcurl4-nss-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore PYCURL_SSL_LIBRARY=nss
COPY requirements.txt .
RUN python -m venv venv \
 && /venv/bin/pip install -r requirements.txt
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
RUN /venv/bin/pip install --no-deps .

FROM docker.io/library/python:3.10-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends libcurl3-nss \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /venv /venv
RUN mkdir /data
WORKDIR /data
VOLUME /data
EXPOSE 8888
CMD ["/venv/bin/an-website"]
