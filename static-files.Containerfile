# syntax=docker.io/docker/dockerfile:1.24
# check=error=true;experimental=InvalidDefinitionDescription

ARG AN_WEBSITE=ghcr.io/asozialesnetzwerk/an-website:dev
ARG BASE=docker.io/library/debian:trixie-slim

FROM $AN_WEBSITE AS static_files
SHELL [ "/venv/bin/python", "-c" ]
RUN <<EOF
from os import mkdir
from pathlib import Path
from shutil import copytree as copy_files

from an_website.main import get_all_handlers, get_module_infos
from an_website.utils.static_file_from_traversable import TraversableStaticFileHandler

mkdir("/static")

paths: list[tuple[Path, str]] = []
for path, handler, data in get_all_handlers(get_module_infos()):
    if not (
        path.endswith("(.*)")
        and handler is TraversableStaticFileHandler
    ):
        continue
    disk_path = data["root"].absolute().resolve()
    disk_path_string = disk_path.as_posix()
    assert disk_path_string.startswith("/"), f"{disk_path_string!r} should start with /"

    if disk_path_string == "/data/.well-known":
        continue

    assert path.startswith("/")
    paths.append((disk_path, f"/static{path}".removesuffix("/(.*)")))

paths.sort(key=lambda t: len(t[1]))
for path, dest in paths:
    print("COPYING", path, "to", dest)
    copy_files(path, dest)
EOF

FROM $BASE
COPY --from=static_files /static /static
COPY ./scripts/vendored/content-negotiation.lua /
RUN <<EOF
    set -xeu
    apt-get update
    apt-get install -y --no-install-recommends lighttpd lighttpd-mod-magnet
    rm -fr /var/lib/apt/lists/*

    printf '%s\n' '
-- the v query parameter is used to bust the cache
-- if the v query parameter is set, assume files immutable
local query = lighty.c.urldec_query(lighty.r.req_attr["uri.query"])
if query["v"] then
    lighty.r.resp_header["Cache-Control"] = "public,immutable,max-age=315360000"
    lighty.r.resp_header["Last-Modified"] = nil
    lighty.r.resp_header["ETag"] = nil
end
' > /version-query.lua

    printf '%s\n' \
        'server.port = 80' \
        'server.modules += ("mod_magnet")' \
        'server.document-root = "/static/"' \
        'magnet.attract-physical-path-to = ( "/content-negotiation.lua"  )' \
        'magnet.attract-response-start-to = ( "/version-query.lua" )' \
        > /lighttpd.conf
EOF
EXPOSE 80
ENTRYPOINT ["lighttpd", "-D", "-f", "/lighttpd.conf"]
