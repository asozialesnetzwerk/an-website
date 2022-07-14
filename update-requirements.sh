#!/bin/sh
set -e

export PIPENV_VERBOSITY=-1

pipenv verify

pipenv requirements --exclude-markers > requirements.txt
pipenv requirements --exclude-markers --dev > requirements-dev.txt

#remove global options
sed -i "/^-/d" requirements.txt
sed -i "/^-/d" requirements-dev.txt

#remove per-requirement options
#sed -i "s/ -.*//" requirements.txt
#sed -i "s/ -.*//" requirements-dev.txt

#remove trailing spaces
#sed -i "s/ *$//" requirements.txt
#sed -i "s/ *$//" requirements-dev.txt

#remove empty lines
#sed -i "/^$/d" requirements.txt
#sed -i "/^$/d" requirements-dev.txt

#remove markers
#sed -i "s/;.*//" requirements.txt
#sed -i "s/;.*//" requirements-dev.txt