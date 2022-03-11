# Webseite des AN
[![Deploy](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/deploy.yml)
[![Check code](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/check.yml)
[![Check emoji](https://github.com/asozialesnetzwerk/an-website/actions/workflows/emoji-in-commit.yml/badge.svg)](https://github.com/asozialesnetzwerk/an-website/actions/workflows/emoji-in-commit.yml)
[![Code coverage](https://asozialesnetzwerk.github.io/an-website/coverage/badge.svg)](https://asozialesnetzwerk.github.io/an-website/coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1.svg?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort)

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
### Linux (tested with Arch Linux):
You need:
- CPython 3.10+
- Packages from requirements.txt (`pip install -r requirements.txt`)
- Supervisord
- Redis 6.2+
- redis-cell (for ratelimits)
- Elasticsearch 7.17 or 8.x
- UwUFetch
- Git

How:
- Clone this repo in the home directory of a user
- Add the following at the end of /etc/supervisord.conf (if necessary)
```
  [include]
  files = /etc/supervisor.d/*.ini
```
- Create /etc/supervisor.d/ (if necessary)
- Run restart.sh as the user of the home directory

### FreeBSD
Should work similar to Linux.
`/etc/supervisord.conf`   -> `/usr/local/etc/supervisord.conf`
`/etc/supervisor.d/*.ini` -> `/usr/local/etc/supervisor.d/*.ini`
`/etc/supervisor.d/`      -> `/usr/local/etc/supervisor.d/`
restart.sh: `/etc/supervisor.d/$SERVICE_FILE_NAME` -> `/usr/local/etc/supervisor.d/$SERVICE_FILE_NAME`

### macOS
Not supported, but should work.

### Windows
Not supported, but maybe works.
