#!/bin/sh
set -eu

export PIPENV_VERBOSITY=-1

pipenv verify

pipenv requirements > pip-requirements.txt
pipenv requirements --dev > pip-dev-requirements.txt
pipenv requirements --dev --exclude-markers > pip-constraints.txt

sed -i "/^-/d" pip-requirements.txt
sed -i "/^-/d" pip-dev-requirements.txt
sed -i "/^-/d" pip-constraints.txt

sed -i "s/\[.*\]//" pip-constraints.txt
