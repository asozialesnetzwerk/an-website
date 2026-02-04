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

PYCURL_VERSION="$(python -c 'print(*[l.split(";")[0].split("==")[1] for l in open("pip-requirements.txt") if l.startswith("pycurl==")])')"
PY_CURL_SDIST_URL="$(curl -sSf https://pypi.org/pypi/pycurl/json | jq -r '.releases["'"${PYCURL_VERSION}"'"][] | select(.packagetype == "sdist") | .url')"
sed -i "s|^pycurl==${PYCURL_VERSION}|pycurl @ ${PY_CURL_SDIST_URL} |" pip-requirements.txt pip-dev-requirements.txt
