# Webseite des AN

![License](https://img.shields.io/pypi/l/an-website?label=License)
![Python](https://img.shields.io/pypi/pyversions/an-website?label=Python)
![Implementation](https://img.shields.io/pypi/implementation/an-website?label=Implementation)
[![PyPI](https://img.shields.io/pypi/v/an-website.svg?label=PyPI)](https://pypi.org/project/an-website)\
[![Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/Imports-isort-1674b1.svg?labelColor=ef8336)](https://pycqa.github.io/isort)
[![Coverage](https://asozialesnetzwerk.github.io/an-website/coverage/badge.svg)](https://asozialesnetzwerk.github.io/an-website/coverage)
![Total lines](https://img.shields.io/tokei/lines/github/asozialesnetzwerk/an-website?label=Total%20lines)\
[![Downloads](https://pepy.tech/badge/an-website)](https://pepy.tech/project/an-website)
[![Downloads](https://pepy.tech/badge/an-website/month)](https://pepy.tech/project/an-website)
[![Downloads](https://pepy.tech/badge/an-website/week)](https://pepy.tech/project/an-website)\
[![Check](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml)
[![Deploy](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml)
[![Release](https://github.com/asozialesnetzwerk/an-website/actions/workflows/release.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/release.yml)

## Large Language Models

Do not submit any code or prose written or modified by large language models or
"artificial intelligence" such as GitHub Copilot or ChatGPT to this project.
These tools produce code that looks plausible, which means that not only is it
likely to contain bugs those bugs are likely to be difficult to notice on
review. In addition, because these models were trained indiscriminately and
non-consensually on open-source code with a variety of licenses, it's not
obvious that we have the moral or legal right to redistribute code they
generate.

## How to develop

You need:

- Git (obviously)
- CPython 3.12+
- Packages from pip-dev-requirements.txt
- C and C++ compiler for some of the dependencies
- Depending on the used version of CPython: Rust
- [Just](https://just.systems/man/en/introduction.html)
- For formatting TypeScript and Markdown: [dprint](https://dprint.dev/)
- For building JavaScript and CSS: [Deno](https://deno.com/)\
  (`just build`)
- For linting TypeScript: Node.js and pnpm\
  (`corepack enable` or `alias pnpm="corepack pnpm"`)

### How to check

- `./check.sh`

### How to run

- `python -Xdev -Xwarn_default_encoding -m an_website --redis-enabled=1 --ratelimits=0 --port=8080`

(`-Xdev` enables development mode)

## How to run (production)

### Linux

You need:

- CPython 3.12+
- C and C++ compiler for some of the dependencies
- Depending on the used version of CPython: Rust
- Supervisord
- Redis 6.2
- redis-cell (for ratelimits)
- Elasticsearch 8.12+
- UwUFetch

How:

- [Create a virtual environment](https://docs.python.org/3/library/venv.html)
- Install an-website in the venv (`pip install an-website`)
- create a `config.ini` and configure it
- run it (`an-website` / `python -m an_website`) with Supervisord

### FreeBSD

Should work similar to Linux.

### macOS

Not supported, but should work.

### Windows

Not supported, but maybe works.
