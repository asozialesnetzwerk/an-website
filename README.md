# Webseite des AN

## How to run:
### Linux (tested with arch):
You need:
- python3.9
- packages from requirements.txt
- supervisord

How:
- clone this repo in the home directory of a user
- (if necessary) add the following at the end of /etc/supervisord.conf
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
`/etc/supervisord.conf`   -> `/usr/local/etc/supervisord.conf`  
`/etc/supervisor.d/*.ini` -> `/usr/local/etc/supervisor.d/*.ini`  
`/etc/supervisor.d/`      -> `/usr/local/etc/supervisor.d/`  
restart.sh: `/etc/supervisor.d/$SERVICE_FILE_NAME` -> `/usr/local/etc/supervisor.d/$SERVICE_FILE_NAME`

### MacOS:
Why? (same as FreeBSD, probably)
