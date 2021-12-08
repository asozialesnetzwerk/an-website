#!/bin/sh

SERVICE_FILE_NAME="an_website.ini"
SERVICE_FILE_LOCATION="/etc/supervisor.d/$SERVICE_FILE_NAME"

# if it is in detached head state:
if [ -z "$(git branch --show-current)" ]
then
    echo "checkout to main branch"
    git checkout main
fi

echo "get latest files from git"
git pull --rebase --autostash

# install required packages:
if [ ! -d "venv" ]
then
    echo "venv doesn't exist, so create it"
    python3 -m venv venv
fi

# if there's an argument use that commit hash
if [ -n "$1" ]
then
    echo "checkout to git hash: '$1'"
    git checkout "$1"
fi


venv/bin/pip install --disable-pip-version-check -U -r requirements.txt

if [ ! -f "$SERVICE_FILE_LOCATION" ]
then
    echo "supervisord config doesn't exist, so create it"
    sudo touch "$SERVICE_FILE_LOCATION"
    echo "Let the user be the owner"
    sudo chown "$USER" "$SERVICE_FILE_LOCATION"
fi

echo "Update the supervisord config in $SERVICE_FILE_LOCATION"
sed "s/<user>/$USER/g" "$SERVICE_FILE_NAME" \
  | sed "s|<home>|$HOME|g" \
  | sed "s/<lang>/$LANG/g" > "$SERVICE_FILE_LOCATION"

# if the second argument is "no_restart"
if [ -n "$2" ] && [ "$2" = "no_restart" ]
then
    exit 0
fi

echo "Restart an_website"
sudo supervisorctl reread
sudo supervisorctl stop an_website
sudo supervisorctl remove an_website
sudo supervisorctl add an_website
echo "Finished restarting"
