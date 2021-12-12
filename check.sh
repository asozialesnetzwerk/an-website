#!/bin/sh

#if [ -d venv ];
#then
#    . venv/bin/activate
#    python3 -m pip install --disable-pip-version-check -U -r requirements-dev.txt --quiet
#else
#    python3 -m pip install --disable-pip-version-check -U -r requirements-dev.txt --quiet --user
#fi

# install pre-commit hooks
pre-commit install

# test hashing files (important to see if umlaute are used)
git ls-files | xargs sha1sum | sha1sum | cut -d ' ' -f 1

# check for errors
echo Pyflakes:
python3 -m pyflakes an_website tests || exit 1

# sort imports
echo isort:
python3 -m isort an_website tests

# check formatting
echo Black:
python3 -m black --check --diff --color an_website tests || echo 'Run "python3 -m black an_website tests" to reformat.'

# check types
echo mypy:
python3 -m mypy --pretty -p an_website -p tests

# lint
echo Flake8:
python3 -m flake8 --extend-ignore=D100,D101,D102,D103,D104,E501 an_website tests
echo Pylint:
python3 -m pylint --output-format=colorized -e useless-suppression an_website tests

# run tests
echo Tests:
python3 -m coverage run --source=an_website -m py.test tests/

echo 'Run "python3 -m coverage report" to show the coverage'
