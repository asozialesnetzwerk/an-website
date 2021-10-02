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
  | sed "s/<home>/$HOME/g" \
  | sed "s/<lang>/$LANG/g" \
  | sed "s/<lc_all>/$LC_ALL/g" > "$SERVICE_FILE_LOCATION"

echo "Reread config"
sudo supervisorctl reread
echo "Restart an_website"
sudo supervisorctl restart an_website

echo "Finished restarting"
