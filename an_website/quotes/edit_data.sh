#!/bin/sh

# This script is used to edit the data of a quote or author.
# To use it call it with the api key as the argument.
# You'll need jq installed to use this script.

# To get an api key go to https://zitate.prapsschnalinen.de/
API_KEY="$1"

echo "Enter the type [a|q]"
read -r TYPE

if [ "$TYPE" = "a" ]; then
  URL="https://zitate.prapsschnalinen.de/api/authors"
  KEY_NAME="author"
  TYPE_TEXT="author name"
elif [ "$TYPE" = "q" ]; then
  URL="https://zitate.prapsschnalinen.de/api/quotes"
  KEY_NAME="quote"
  TYPE_TEXT="quote text"
else
  echo "Invalid type, has to be either q or a."
  exit 1
fi

echo "Please enter the id"
read -r ID

REMOTE_DATA=$(curl -s "$URL/$ID")
CURR_VALUE=$(echo "$REMOTE_DATA" | jq ".$KEY_NAME")

echo "$REMOTE_DATA"

echo "Please enter the new $TYPE_TEXT"
read -r NEW_VALUE

echo "Do you want to replace $CURR_VALUE with \"$NEW_VALUE\"?"

# echo "Url:  $URL"
# echo "Data: key=$API_KEY&id=$ID&$KEY_NAME=$NEW_VALUE"

echo "Enter y to confirm, anything else to abort."

read -r CONFIRM

if [ "$CONFIRM" = "y" ]; then
  curl --data-urlencode "key=$API_KEY" --data-urlencode "id=$ID" --data-urlencode "$KEY_NAME=$NEW_VALUE" "$URL"
else
  echo "Aborted."
fi
