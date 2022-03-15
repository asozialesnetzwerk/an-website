#!/bin/sh

if [ -d venv ]
then
    . venv/bin/activate
fi

set -e
python -m pip install --disable-pip-version-check --require-virtualenv --quiet -r requirements-dev.txt
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
mypy --pretty -p an_website -p test

# lint
echo Flake8:
flake8 --extend-ignore=D100,D102 *.py an_website test
echo Pylint:
pylint --output-format=colorized *.py an_website test

if [ -n $1 ] && [ $1 = "test" ]
then
    # run tests
    echo Tests:
    pytest --cov-report= --cov=an_website test
    echo 'Run "coverage report" to show the coverage'
fi
