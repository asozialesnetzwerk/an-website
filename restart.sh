#!/bin/sh

SERVICE_FILE_NAME="an-website.service"
SERVICE_FILE_LOCATION="$HOME/.config/systemd/user/"

# get latest files from git:
git pull

mkdir -p "$SERVICE_FILE_LOCATION"

# update the service file
sed "s/user-placeholder/$USER/g" "$SERVICE_FILE_NAME" > "$SERVICE_FILE_LOCATION$SERVICE_FILE_NAME"

# enable the service
systemctl --user enable "$SERVICE_FILE_NAME"
# restart the service
systemctl --user restart "$SERVICE_FILE_NAME"