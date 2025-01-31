default:
    @just --list --justfile "{{ justfile() }}"

do-it:
    @xdg-open https://youtu.be/AkygX8Fncpk

clean: clean_css clean_js
    ./scripts/compress_static_files.py --clean

clean_css:
    rm -fr "{{ justfile_directory() }}/an_website/static/css"

clean_js:
    rm -fr "{{ justfile_directory() }}/an_website/static/js"

build:
    -@just build_js 2> /dev/null
    @just build_css
    @just build_js

[positional-arguments]
build_css *args:
    @just esbuild --outbase=style --outdir=an_website/static/css 'style/**/*.css' "$@"

[positional-arguments]
build_js_debug *args:
    @just esbuild an_website/**/*[!_].ts --bundle '--external:/static/*' --legal-comments=inline '--footer:js=// @license-end' --format=esm --outbase=an_website --outdir=an_website/static/js "--alias:@utils/utils.js=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" "$@"

[positional-arguments]
build_js *args:
    @just build_js_debug '--pure:console.log' '--pure:console.debug' "$@"

[positional-arguments]
esbuild *args:
    deno run -A https://deno.land/x/esbuild@v0.24.2/mod.js "--target=$(just target),chrome103,edge129,firefox115,ios11,opera114,safari15.6" --charset=utf8 --minify --sourcemap --tree-shaking=false "$@"

target:
    #!/usr/bin/env python3
    year = {{ datetime_utc('%Y') }}
    month = {{ trim_start_match(datetime_utc('%m'), '0') }}
    print(f"es{min(year - (5 + (month < 7)), 2022)}")

watch_css: (build_css '--watch')

watch_js: (build_js '--watch')

watch_js_debug: (build_js_debug '--watch')

watman:
    @deno eval 'console.log(Array(16).join("wat" - 1) + " Batman!")'
