# Webseite des AN

## How to run:
### Linux (tested with arch):
You need:
- pypy3 (if you want to use another python you need to edit some files)
- packages from requirements.txt
- supervisord

How:
- clone this repo in the home directory of a user
- (if necessary) add the following to the end of /etc/supervisord.conf
```
  [include]
  files = /etc/supervisor.d/*.ini
```
- (if necessary) create /etc/supervisor.d/
- run restart.sh as the user of the home directory

### Windows:
DO NOT USE WINDOWS

### FreeBSD:
should work similar to linux

### MacOS:
Why? (same as FreeBSD)
