#!/bin/sh

# This script is used to edit the data of a quote or author.
# To use it call it with the api key as the argument.
# You'll need jq installed to use this script.

# To get an api key go to https://zitate.prapsschnalinen.de
API_KEY="$1"
API_BASE_URL="https://zitate.prapsschnalinen.de/api"

echo "Enter the type [a|q]"
read -r TYPE

if [ "${TYPE}" = "a" ]; then
  URL="${API_BASE_URL}/authors"
  KEY_NAME="author"
  TYPE_TEXT="author name"
elif [ "${TYPE}" = "q" ]; then
  URL="${API_BASE_URL}/quotes"
  KEY_NAME="quote"
  TYPE_TEXT="quote text"
else
  echo "Invalid type, has to be either q or a."
  exit 1
fi

echo "Please enter the id"
read -r ID

REMOTE_DATA=$(curl -s "${URL}/${ID}")
CURRENT_VALUE=$(echo "${REMOTE_DATA}" | jq ".${KEY_NAME}")

echo "https://asozial.org/zitate/info/${TYPE}/${ID}"
echo "${REMOTE_DATA}"
# get and output the real quotes with the author
if [ "${TYPE}" = "a" ]; then
  curl -s "${API_BASE_URL}/quotes?author=${ID}"
fi

echo "Please enter the new ${TYPE_TEXT}"
read -r NEW_VALUE

echo "Do you want to replace ${CURRENT_VALUE} with \"${NEW_VALUE}\"?"

# echo "URL:  ${URL}"
# echo "Data: key=${API_KEY}&id=${ID}&$KEY_NAME=${NEW_VALUE}"

echo "Enter y to confirm, anything else to abort."

read -r CONFIRM

if [ "${CONFIRM}" = "y" ]; then
  curl --data-urlencode "key=${API_KEY}" --data-urlencode "id=${ID}" --data-urlencode "${KEY_NAME}=${NEW_VALUE}" "${URL}"
else
  echo "Aborted."
fi
