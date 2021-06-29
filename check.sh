#!/bin/sh

if [ -d venv ];
then
    . venv/bin/activate
    python3 -m pip install --disable-pip-version-check -U -r check-requirements.txt --quiet
else
    python3 -m pip install --disable-pip-version-check -U -r check-requirements.txt --quiet --user
fi


# test hashing files (important to see if umlaute are used)
git ls-files | xargs sha1sum | sha1sum | cut -d ' ' -f 1

# check for errors
echo Pyflakes:
python3 -m pyflakes an_website || exit 1

# sort imports
echo isort:
python3 -m isort an_website

# check formatting
echo Black:
python3 -m black --check --diff --color an_website || echo 'Run "python3 -m black an_website" to reformat.'

# check types
echo mypy:
python3 -m mypy --pretty -p an_website

# lint
echo Flake8:
python3 -m flake8 --extend-ignore=D100,D101,D102,D103,D104,E501 an_website
echo Pylint:
python3 -m pylint --output-format=colorized an_website
