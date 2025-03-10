default:
    @just --list --justfile "{{ justfile() }}"

do_it:
    @mpv https://youtu.be/AkygX8Fncpk

clean: clean_compressed clean_css clean_js

clean_css:
    rm -fr "{{ justfile_directory() }}/an_website/static/css"

clean_js:
    rm -fr "{{ justfile_directory() }}/an_website/static/js"

clean_compressed:
    ./scripts/compress_static_files.py --clean

build:
    -@just build_js 2> /dev/null
    @just build_css
    @just build_js

[positional-arguments]
build_css *args:
    @just esbuild --outbase=style --outdir=an_website/static/css 'style/**/*.css' "$@"

[positional-arguments]
build_js_debug *args:
    @find an_website -regex '.*[^_]\.tsx?' -exec just _build_single_js_file_debug '{}' "$@" ';'

[positional-arguments]
_build_single_js_file_debug *args:
    #!/bin/sh
    set -eu
    FILE="${1}"
    shift
    just esbuild "${FILE}" \
        --jsx-import-source=@utils --jsx=automatic \
        "--banner:js=$(head -n1 "${FILE}")" \
        '--footer:js=// @license-end' \
        '--legal-comments=none' \
        --bundle '--external:/static/*' \
        --format=esm --outbase=an_website --outdir=an_website/static/js \
        "--alias:@utils/utils.js=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" \
        "--alias:@utils/jsx-runtime=$(./scripts/fix_static_url_path.py /static/js/utils/jsx-runtime.js)" \
        "$@"

[positional-arguments]
build_js *args:
    @just build_js_debug '--pure:console.log' '--pure:console.debug' "$@"

[positional-arguments]
esbuild *args:
    deno run -A https://deno.land/x/esbuild@v0.25.0/mod.js \
        "--target=$(just target),chrome103,edge129,firefox115,ios11,opera114,safari15.6" \
        --charset=utf8 --minify --sourcemap --tree-shaking=false "$@"

target:
    #!/usr/bin/env python3
    year = {{ datetime_utc('%Y') }}
    month = {{ trim_start_match(datetime_utc('%m'), '0') }}
    print(f"es{min(year - (5 + (month < 7)), 2022)}")

watch_css: (build_css '--watch')

watch_js: (build_js '--watch')

watch_js_debug: (build_js_debug '--watch')

wat:
    @deno eval 'console.log(Array(16).join("wat" - 1) + " Batman!")'
