#!/bin/sh

if [ -d venv ];
then
    . venv/bin/activate
    python3 -m pip install --disable-pip-version-check -r requirements-dev.txt --quiet
else
    python3 -m pip install --disable-pip-version-check -r requirements-dev.txt --quiet --user
fi

# install pre-commit hooks
pre-commit install

# test hashing files (important to see if umlaute are used)
git ls-files | xargs sha1sum | sha1sum | cut -d ' ' -f 1

# sort imports
echo isort:
python3 -m isort .

# check formatting
echo Black:
python3 -m black --check --diff --color . || echo 'Run "python3 -m black ." to reformat.'

# check types
echo mypy:
python3 -m mypy --pretty --warn-unused-ignores --warn-redundant-casts -p an_website -p tests

# lint
echo Flake8:
python3 -m flake8 --extend-ignore=D100,D102 an_website tests
echo Pylint:
python3 -m pylint --output-format=colorized an_website tests

# run tests
echo Tests:
python3 -m pytest --cov-report= --cov=an_website tests

echo 'Run "python3 -m coverage report" to show the coverage'
