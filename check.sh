#!/bin/sh

if [ -d venv ]; then
  if ! . venv/bin/activate; then
    echo "Activating venv failed."
    echo "You have a venv directory, but it isn't a valid Python virtual environment."
    echo 'Either run "rm -r venv" or run "python -m venv venv".'
    exit 1
  fi
fi

pip_install="python3 -m pip install --disable-pip-version-check --require-virtualenv --quiet"
$pip_install "pip>=22.2" wheel
if [ $? -ne 0 -a $? -ne 3 ]; then
  echo "Installing pip>=22.2 and wheel failed."
  exit 1
fi
$pip_install -r requirements-dev.txt
if [ $? -ne 0 -a $? -ne 3 ]; then
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
mypy --pretty -p an_website -p tests -p scripts || FAILED=$(( 8 | FAILED ))

# lint
echo Flake8:
flake8 --extend-ignore=D102 setup.py an_website tests scripts || FAILED=$(( 16 | FAILED ))
echo Pylint:
pylint="pylint --output-format=colorized"
$pylint -d all -e fixme --score=no --persistent=no setup.py an_website tests scripts
$pylint -d fixme setup.py an_website tests scripts || FAILED=$(( 32 | FAILED ))

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
