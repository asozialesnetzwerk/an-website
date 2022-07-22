#!/bin/sh

if [ -d venv ]; then
  if ! . venv/bin/activate; then
    echo "Activating venv failed."
    echo "You have a venv directory, but it isn't a valid python venv."
    echo 'Either run "rm -r venv" or run "python -m venv venv".'
    exit 1
  fi
fi

pip_install="python3 -m pip install --disable-pip-version-check --require-virtualenv --quiet"
if ! $pip_install "pip>=22.2"; then
  echo "Installing pip>=22.2 failed."
  exit 1
fi
if ! $pip_install -r requirements-dev.txt; then
  echo "Installing requirements in requirements-dev.txt failed."
  exit 1
fi

# install pre-commit hooks
pre-commit install

FAILED=0

# sort imports
echo isort:
isort . || FAILED=$(( 2 | FAILED ))

# check formatting
echo Black:
if ! black --check --diff --color .; then
  echo 'Run "black ." to reformat.'
  FAILED=$(( 4 | FAILED ))
fi

# check types
echo mypy:
mypy --pretty -p an_website -p tests || FAILED=$(( 8 | FAILED ))

# lint
echo Flake8:
flake8 --extend-ignore=D102 ./*.py an_website tests || FAILED=$(( 16 | FAILED ))
echo Pylint:
pylint="pylint --output-format=colorized"
$pylint -d all -e fixme --score=no --persistent=no ./*.py an_website tests
$pylint -d fixme ./*.py an_website tests || FAILED=$(( 32 | FAILED ))

if [ -n "$1" ]; then
  pytest="pytest --durations=0 --durations-min=0.5"
  if [ "$1" = "test" ]; then
    echo Tests:
    $pytest tests || FAILED=$(( 64 | FAILED ))
  elif [ "$1" = "test-cov" ]; then
    echo Tests:
    $pytest --cov=an_website --cov-report= tests || FAILED=$(( 64 | FAILED ))
    echo Coverage:
    coverage report --precision=3 --sort=cover --skip-covered
  fi
fi

exit "$FAILED"
