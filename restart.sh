#!/bin/sh

SERVICE_FILE_NAME="an_website.ini"
SERVICE_FILE_LOCATION="/etc/supervisor.d/$SERVICE_FILE_NAME"

# get latest files from git:
git pull --rebase --autostash

# install required packages:
if [ ! -d "venv" ]
then
    # venv doesn't exist, so create it:
    python3 -m venv venv
fi

venv/bin/pip install --disable-pip-version-check -U -r requirements.txt

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
sudo supervisorctl restart an_website
