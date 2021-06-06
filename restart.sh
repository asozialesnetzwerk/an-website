#!/bin/sh

SERVICE_FILE_NAME="an-website.ini"
SERVICE_FILE_LOCATION="/etc/supervisor.d/$SERVICE_FILE_NAME"

# get latest files from git:
git pull --rebase

# install required packages:
if [ ! -d "venv" ]
then
    # venv doesn't exist, so create it:
    pypy3 -m venv venv
fi

. venv/bin/activate

pip install -r requirements.txt

if [ ! -f "$SERVICE_FILE_LOCATION" ]
then
    # File doesn't exist, so create it:
    sudo touch "$SERVICE_FILE_LOCATION"
    # Let the user be the owner:
    sudo chown "$USER" "$SERVICE_FILE_LOCATION"
fi

# update the file
sed "s/user-placeholder/$USER/g" "$SERVICE_FILE_NAME" > "$SERVICE_FILE_LOCATION"

sudo supervisorctl reread
sudo supervisorctl restart an-website
