#!/bin/sh

TARGET="/etc/supervisor.d/an_website.ini"

if [ -n "$1" ]
then
  TARGET="$1"
fi

echo "Writing config to ${TARGET}"

sed -e "s|<home>|${HOME}|g" -e "s/<lang>/${LANG}/g" -e "s/<user>/${USER}/g" "an_website.ini" > "${TARGET}"
