#!/bin/sh

SERVICE_FILE_NAME="an-website.ini"
SERVICE_FILE_LOCATION="/etc/supervisor.d/"

# get latest files from git:
git pull

mkdir -p "$SERVICE_FILE_LOCATION"

# update the file
sed "s/user-placeholder/$USER/g" "$SERVICE_FILE_NAME" > "$SERVICE_FILE_LOCATION$SERVICE_FILE_NAME"

supervisorctl reread
supervisorctl restart an-website
