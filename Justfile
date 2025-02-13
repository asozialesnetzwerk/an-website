export PATH := `. venv/bin/activate && echo "${PATH}"`

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
    @just esbuild an_website/*/*[!_].ts an_website/*/*[!_].tsx an_website/*/*/*[!_].ts an_website/*/*/*[!_].tsx \
        --tree-shaking=true \
        --loader:.svg=text \
        --jsx-import-source=@utils --jsx=automatic \
        --bundle '--external:/static/*' --legal-comments=inline '--footer:js=// @license-end' \
        --format=esm --outbase=an_website --outdir=an_website/static/js \
        "--alias:@utils/utils.js=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" \
        "--alias:@utils/jsx-runtime=$(./scripts/fix_static_url_path.py /static/js/utils/utils.js)" \
        "$@"

[positional-arguments]
build_js *args:
    @just build_js_debug '--pure:console.log' '--pure:console.debug' "$@"

[positional-arguments]
esbuild *args:
    deno run -A https://deno.land/x/esbuild@v0.25.0/mod.js "--target=$(just target),chrome103,edge129,firefox115,ios11,opera114,safari15.6" --charset=utf8 --minify --sourcemap --tree-shaking=false "$@"

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

[group('python')]
[no-exit-message]
check: (requirements '--quiet') setup-precommit
    #!/bin/sh
    FAILED=0
    alias "just=$(command -v just) --set PATH '${PATH}' --one"
    just isort || FAILED=$(( 2 | FAILED ))
    if ! just black --check --diff --color .; then
      echo 'Run "python3 -m black ." to reformat'
      FAILED=$(( 4 | FAILED ))
    fi
    just mypy || FAILED=$(( 8 | FAILED ))
    just flake8 || FAILED=$(( 16 | FAILED ))
    just pylint || FAILED=$(( 32 | FAILED ))
    just bandit || FAILED=$(( 64 | FAILED ))
    exit "$FAILED"

[group('python')]
[no-exit-message]
format: isort black

[group('python')]
[no-exit-message]
[positional-arguments]
@black *args:
    echo {{ BOLD }}black $@ .{{ NORMAL }}
    black  "$@" .

[group('python')]
[no-exit-message]
isort:
    isort .

[group('python')]
requirements arg="--require-virtualenv": (pip_install arg 'pip>=25.0') (pip_install arg '-r' 'pip-dev-requirements.txt')

[positional-arguments]
[private]
@pip_install *args:
    pip install --disable-pip-version-check --require-virtualenv "$@"

[group('python')]
[no-exit-message]
mypy:
    mypy --pretty

[group('python')]
[no-exit-message]
flake8:
    flake8 --show-source

[group('python')]
@pylint $DISABLE_PYSTON="1":
    echo "{{ BOLD }}pylint .{{ NORMAL }}"
    pylint -d all -e fixme --exit-zero --score=no --persistent=no .
    pylint -d fixme .

[group('python')]
[no-exit-message]
bandit:
    bandit -qrc pyproject.toml .

[group('python')]
[no-exit-message]
[positional-arguments]
test *args:
    pytest --durations=0 --durations-min=0.5 "$@"

[group('python')]
[no-exit-message]
test-cov:
    @just test --cov --cov-report=term:skip-covered

[group('python')]
@setup-precommit:
    python3 -m pre_commit install
