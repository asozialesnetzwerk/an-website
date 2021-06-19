#!/bin/sh

venv/bin/python3 -m pip install -r check-requirements.txt

# test hashing files (important to see if umlaute are used):
git ls-files | xargs sha1sum | sha1sum

# fix code:
echo black:
venv/bin/black -t py38 .
echo isort:
venv/bin/isort .

# Check for errors
echo pyflakes:
venv/bin/pyflakes an_website

# lint:
echo pylint:
venv/bin/pylint -d R,line-too-long an_website

# Check types:
echo mypy:
venv/bin/mypy --show-column-numbers --show-error-codes -p an_website
