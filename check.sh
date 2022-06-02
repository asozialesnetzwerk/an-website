#!/bin/sh

if [ -d venv ]
then
    . venv/bin/activate
fi

set -e
python3 -m pip install --disable-pip-version-check --require-virtualenv --quiet "pip>=22.0"
python3 -m pip install --disable-pip-version-check --require-virtualenv --quiet -r requirements-dev.txt
set +e

# install pre-commit hooks
pre-commit install

# sort imports
echo isort:
isort .

# check formatting
echo Black:
black --check --diff --color . || echo 'Run "black ." to reformat'

# check types
echo mypy:
mypy --pretty -p an_website -p tests

# lint
echo Flake8:
flake8 --extend-ignore=D102 ./*.py an_website tests
echo Pylint:
pylint --output-format=colorized ./*.py an_website tests

if [ -n "$1" ]; then
  if [ "$1" = "test" ]; then
    echo Tests:
    pytest --failed-first --durations=0 --durations-min=0.5 tests
  elif [ "$1" = "test-cov" ]; then
    echo Tests:
    pytest --failed-first --durations=0 --durations-min=0.5 --cov=an_website --cov-report= tests
    echo Coverage:
    coverage report --precision=3 --sort=cover --skip-covered
  fi
fi
