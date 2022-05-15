# Webseite des AN
![License](https://img.shields.io/pypi/l/an-website?label=License)
![Python](https://img.shields.io/pypi/pyversions/an-website?label=Python)
![Implementation](https://img.shields.io/pypi/implementation/an-website?label=Implementation)
[![PyPI](https://img.shields.io/pypi/v/an-website.svg?label=PyPI)](https://pypi.org/project/an-website)\
[![Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/Imports-isort-1674b1.svg?labelColor=ef8336)](https://pycqa.github.io/isort)
[![Coverage](https://asozialesnetzwerk.github.io/an-website/coverage/badge.svg)](https://asozialesnetzwerk.github.io/an-website/coverage)
![Total lines](https://img.shields.io/tokei/lines/github/asozialesnetzwerk/an-website?label=Total%20lines)\
[![Check](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml)
[![Deploy](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml)
[![Release](https://github.com/asozialesnetzwerk/an-website/actions/workflows/release.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/release.yml)

## How to develop
You need:
- Git (obviously)
- CPython 3.10
- Packages from requirements-dev.txt (`pip install -r requirements-dev.txt`)

### How to check
- `./check.sh`

### How to run
- `python -Xdev -m an_website` (`-Xdev` enables development mode)

## How to run (production)
### Linux
You need:
- CPython 3.10
- Supervisord
- Redis 6.2
- redis-cell (for ratelimits)
- Elasticsearch 7.17 or 8.x
- UwUFetch

How:
- [Create a virtual environment](https://docs.python.org/3/library/venv.html)
- Install an-website in the venv (`pip install an-website`)
- ??? (TODO: finish instructions)

### FreeBSD
Should work similar to Linux.

### macOS
Not supported, but should work.

### Windows
Not supported, but maybe works.
