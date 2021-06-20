#!/bin/sh

if [ -d venv ];
then
    . venv/bin/activate
    python3 -m pip install -r check-requirements.txt --quiet
else
    python3 -m pip install --user -r check-requirements.txt --quiet
fi


# test hashing files (important to see if umlaute are used)
git ls-files | xargs sha1sum | sha1sum | cut -d ' ' -f 1

# check for errors
echo Pyflakes:
python3 -m pyflakes an_website || exit 1

# sort imports
echo isort:
python3 -m isort .

# check formatting
echo Black:
python3 -m black -t py38 --check --diff --color . || echo 'Run "python3 -m black -t py38 ." to reformat.'

# check types
echo mypy:
python3 -m mypy --show-column-numbers --show-error-codes --pretty -p an_website

# lint
echo Pylint:
python3 -m pylint --output-format=colorized an_website
