#!/bin/sh

SERVICE_FILE_NAME="an-website.service"
SERVICE_FILE_LOCATION="/etc/systemd/system/$SERVICE_FILE_NAME"

# get latest files from git:
git pull

if [ ! -f "SERVICE_FILE_LOCATION" ]
then
    # File doesn't exist, so create it:
    sudo touch "SERVICE_FILE_LOCATION"
    # Let the user be the owner:
    sudo chown "$USER" "SERVICE_FILE_LOCATION"
fi

# update the service file
sed "s/user-placeholder/$USER/g" "$SERVICE_FILE_NAME" > "SERVICE_FILE_LOCATION"

# enable the service
systemctl enable "$SERVICE_FILE_NAME"
# restart the service
systemctl restart "$SERVICE_FILE_NAME"