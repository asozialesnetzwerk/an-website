# Webseite des AN
[![Deploy](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml)
[![Check code](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml)
[![Check emoji](https://github.com/asozialesnetzwerk/an-website/actions/workflows/emoji.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/emoji-in-commit.yml)
[![Code coverage](https://asozialesnetzwerk.github.io/an-website/coverage/badge.svg)](https://asozialesnetzwerk.github.io/an-website/coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1.svg?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)
[![Daily build](https://github.com/asozialesnetzwerk/an-website/actions/workflows/daily.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/daily.yml)

## How to develop
You need:
- CPython 3.10+
- Packages from requirements-dev.txt (`pip install -r requirements-dev.txt`)
- Git (obviously)

### How to check
- `./check.sh`

### How to run
- `python -Xdev -m an_website` (`-Xdev` enables development mode)


## How to run (production)
### Linux
You need:
- CPython 3.10+
- Supervisord
- Redis 6.2+
- redis-cell (for ratelimits)
- Elasticsearch 7.17 or 8.x
- UwUFetch

How:
- Create a venv somewhere (for example `/opt/an-website`)
- Install an-website in the venv (`pip install git+https://github.com/asozialesnetzwerk/an-website.git`)
- ??? (TODO: finish instructions)

### FreeBSD
Should work similar to Linux.

### macOS
Not supported, but should work.

### Windows
Not supported, but maybe works.
