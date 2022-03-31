#!/bin/sh
set -e

export PIPENV_VERBOSITY=-1

pipenv verify

pipenv lock -r > requirements.txt
pipenv lock -r -d > requirements-dev.txt

#remove markers
sed -i "s/;.*//" requirements.txt
sed -i "s/;.*//" requirements-dev.txt

#remove lines not starting with a letter
sed -n -i "/^\w/p" requirements.txt
sed -n -i "/^\w/p" requirements-dev.txt
