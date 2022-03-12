#!/bin/sh

SERVICE_FILE_NAME="an_website.ini"
SERVICE_FILE_LOCATION="/etc/supervisor.d/$SERVICE_FILE_NAME"

# if there's an argument
if [ -n $1 ]
then
    echo "git fetch origin $1"
    git fetch origin $1
    echo "git checkout $1"
    git checkout $1
else
    # if it is in detached head state
    if [ -z "$(git branch --show-current)" ]
    then
        echo "git checkout main"
        git checkout main
    fi
    echo "git pull --rebase --autostash"
    git pull --rebase --autostash
fi

if [ ! -d "venv" ]
then
    echo "python3 -m venv venv"
    python3 -m venv venv
fi

echo "venv/bin/pip install --disable-pip-version-check -U -r requirements.txt"
venv/bin/pip install --disable-pip-version-check -U -r requirements.txt

if [ ! -f $SERVICE_FILE_LOCATION ]
then
    echo "sudo touch $SERVICE_FILE_LOCATION"
    sudo touch $SERVICE_FILE_LOCATION
    echo "sudo chown $USER $SERVICE_FILE_LOCATION"
    sudo chown $USER $SERVICE_FILE_LOCATION
fi

echo 'sed -e "s/<user>/$USER/g" -e "s|<home>|$HOME|g" -e "s/<lang>/$LANG/g" $SERVICE_FILE_NAME > $SERVICE_FILE_LOCATION'
sed -e "s/<user>/$USER/g" -e "s|<home>|$HOME|g" -e "s/<lang>/$LANG/g" $SERVICE_FILE_NAME > $SERVICE_FILE_LOCATION

# if the second argument is "no_restart"
if [ -n $2 ] && [ $2 = "no_restart" ]
then
    exit 0
fi

echo "sudo supervisorctl reread"
sudo supervisorctl reread
echo "sudo supervisorctl stop an_website"
sudo supervisorctl stop an_website
echo "sudo supervisorctl remove an_website"
sudo supervisorctl remove an_website
echo "sudo supervisorctl add an_website"
sudo supervisorctl add an_website
