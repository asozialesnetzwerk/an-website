#!/bin/sh

if [ -d venv ];
then
    . venv/bin/activate
    python -m pip install --disable-pip-version-check -r requirements-dev.txt --quiet
else
    echo 'Please create a Python 3.10+ virtual environment (venv) first'
    echo 'Running "python3.10 -m venv venv" usually works (assuming Python 3.10 is installed)'
    exit 1
fi

# install pre-commit hooks
pre-commit install

# test hashing files (important to see if umlaute are used)
git ls-files | xargs sha1sum | sha1sum | cut -d ' ' -f 1

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
flake8 --extend-ignore=D100,D102 an_website tests
echo Pylint:
pylint --output-format=colorized an_website tests

# run tests
echo Tests:
pytest --cov-report= --cov=an_website tests
echo 'Run "coverage report" to show the coverage'
