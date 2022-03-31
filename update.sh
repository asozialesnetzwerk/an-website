#!/bin/sh
set -e

NAME="an_website"
BRANCH=$(git branch --show-current)

# if there's an argument
if [ -n "$1" ]
then
    echo "git fetch origin \"$1\""
    git fetch origin "$1"
    echo "git checkout \"$1\""
    git checkout "$1"
else
    # if it is in detached head state
    if [ -z "${BRANCH}" ]
    then
        echo "git checkout main"
        git checkout main
    fi
    echo "git pull --rebase --autostash"
    git pull --rebase --autostash
fi

if [ ! -d "/opt/${NAME}/venv" ]
then
    echo "python3 -m venv \"/opt/${NAME}/venv\""
    python3 -m venv "/opt/${NAME}/venv"
fi

echo "\"/opt/${NAME}/venv/bin/pip\" install ."
"/opt/${NAME}/venv/bin/pip" --disable-pip-version-check install .

if [ ! -f "/etc/supervisor.d/${NAME}.ini" ]
then
    echo "sudo touch \"/etc/supervisor.d/${NAME}.ini\""
    sudo touch "/etc/supervisor.d/${NAME}.ini"
    echo "sudo chown \"${USER}\" \"/etc/supervisor.d/${NAME}.ini\""
    sudo chown "${USER}" "/etc/supervisor.d/${NAME}.ini"
fi

echo "sed -e \"s|<home>|${HOME}|g\" -e \"s/<lang>/${LANG}/g\" -e \"s/<user>/${USER}/g\" \"${NAME}.ini\" > \"/etc/supervisor.d/${NAME}.ini\""
sed -e "s|<home>|${HOME}|g" -e "s/<lang>/${LANG}/g" -e "s/<user>/${USER}/g" "${NAME}.ini" > "/etc/supervisor.d/${NAME}.ini"

# if the second argument is "no_restart"
if [ -n "$2" ] && [ "$2" = "no_restart" ]
then
    exit 0
fi

echo "sudo supervisorctl reread"
sudo supervisorctl reread
echo "sudo supervisorctl stop \"${NAME}\""
sudo supervisorctl stop "${NAME}"
echo "sudo supervisorctl remove \"${NAME}\""
sudo supervisorctl remove "${NAME}"
echo "sudo supervisorctl add \"${NAME}\""
sudo supervisorctl add "${NAME}"
