#!/bin/sh
set -eu

export PIPENV_VERBOSITY=-1

pipenv verify

pipenv requirements > requirements.txt
pipenv requirements --dev > requirements-dev.txt
pipenv requirements --exclude-markers --dev > requirements-ci.txt

sed -i "/^-/d" requirements.txt
sed -i "/^-/d" requirements-dev.txt
sed -i "/^-/d" requirements-ci.txt
