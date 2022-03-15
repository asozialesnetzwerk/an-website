#!/bin/sh

PIPENV_VERBOSITY=-1 pipenv lock --keep-outdated -r > requirements.txt
PIPENV_VERBOSITY=-1 pipenv lock --keep-outdated -r --dev > requirements-dev.txt

sed -i "s/;.*//" requirements.txt
sed -i "s/;.*//" requirements-dev.txt
