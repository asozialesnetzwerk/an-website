#!/bin/sh
set -eu

for venv in venv .venv
do
    if [ -d "${venv}" ]; then
        # shellcheck disable=SC1091
        if ! . "${venv}/bin/activate"; then
            echo "Activating venv failed"
            echo "You have a ${venv} directory, but it isn't a valid Python virtual environment"
            echo "Either run 'rm -r ${venv}' or run 'python -m venv ${venv}'"
            exit 1
        fi
        break
    fi
done

pip_install="python3 -m pip install --disable-pip-version-check --require-virtualenv --quiet"
${pip_install} "pip>=24.0"; exit_code="$?"
if [ "${exit_code}" -ne 0 ] && [ "${exit_code}" -ne 3 ]; then
  echo "Installing pip>=24.0 failed"
  exit 1
fi
${pip_install} -r pip-dev-requirements.txt; exit_code="$?"
if [ "${exit_code}" -ne 0 ] && [ "${exit_code}" -ne 3 ]; then
  echo "Installing requirements in pip-dev-requirements.txt failed"
  exit 1
fi

python3 -m pre_commit install || echo 'Running "python3 -m pre_commit install" failed'

FAILED=0

echo isort:
python3 -m isort . || FAILED=$(( 2 | FAILED ))

echo Black:
if ! python3 -m black --check --diff --color .; then
  echo 'Run "python3 -m black ." to reformat'
  FAILED=$(( 4 | FAILED ))
fi

echo mypy:
python3 -m mypy --pretty || FAILED=$(( 8 | FAILED ))

echo Flake8:
python3 -m flake8 --show-source || FAILED=$(( 16 | FAILED ))

echo Pylint:
DISABLE_PYSTON=1 python3 -m pylint -d all -e fixme --exit-zero --score=no --persistent=no .
DISABLE_PYSTON=1 python3 -m pylint -d fixme . || FAILED=$(( 32 | FAILED ))

echo Bandit:
python3 -m bandit -qrc pyproject.toml . || FAILED=$(( 64 | FAILED ))

if [ -n "${1:-}" ]; then
  pytest="python3 -m pytest --durations=0 --durations-min=0.5"
  if [ "${1:-}" = "test" ]; then
    echo Tests:
    ${pytest} || FAILED=$(( 128 | FAILED ))
  elif [ "${1:-}" = "test-cov" ]; then
    echo Tests:
    ${pytest} --cov --cov-report=term:skip-covered || FAILED=$(( 128 | FAILED ))
  fi
fi

exit "${FAILED}"
