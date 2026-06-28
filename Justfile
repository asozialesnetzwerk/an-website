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
    @just esbuild --minify --sourcemap --outbase=style --outdir=an_website/static/css 'style/**/*.css' "$@"

[positional-arguments]
build_js_debug *args:
    @just esbuild an_website/*/*[!_].ts an_website/*/*[!_].tsx an_website/*/*/*[!_].ts an_website/*/*/*[!_].tsx \
        --bundle --format=esm --minify --sourcemap --tree-shaking=true \
        --outbase=an_website --outdir=an_website/static/js \
        --define:DEBUG=true --jsx=automatic --jsx-import-source=@utils \
        '--external:/static/*' --legal-comments=inline '--footer:js=// @license-end' \
        "--alias:@utils/utils.js=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" \
        "--alias:@utils/jsx-runtime=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" \
        --loader:.svg=text \
        "$@"

[positional-arguments]
build_js *args:
    @just build_js_debug '--define:DEBUG=false' '--pure:console.debug' "$@"

[positional-arguments]
esbuild *args:
    deno run -A https://deno.land/x/esbuild@v0.28.1/mod.js \
        --charset=utf8 --supported:destructuring=true \
        "--target=$(just target),chrome103,edge147,firefox115,ios11,safari16.6" \
        "$@"

target:
    #!/usr/bin/env python3
    year = {{ datetime_utc('%Y') }}
    month = {{ trim_start_match(datetime_utc('%m'), '0') }}
    print(f"es{min(year - (5 + (month < 7)), 2022)}")

browsers:
    pnpm browserslist-to-esbuild | sed "s| |,|g"

watch_css: (build_css '--watch')

watch_js: (build_js '--watch')

watch_js_debug: (build_js_debug '--watch')

wat:
    @deno eval 'console.log(Array(16).join("wat" - 1) + " Batman!")'
