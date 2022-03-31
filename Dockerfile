FROM docker.io/library/python:3.10-slim AS builder
RUN apt-get update \
 && apt-get install -y --no-install-recommends git g++ libcurl4-nss-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY . /usr/src/an-website
WORKDIR /usr/src/an-website
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
RUN python -m venv venv \
 && venv/bin/pip install .

FROM docker.io/library/python:3.10-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends libcurl3-nss \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/an-website/venv /opt/an-website
RUN mkdir /data
WORKDIR /data
VOLUME /data
EXPOSE 8080
CMD ["/opt/an-website/bin/python", "-m", "an_website"]
