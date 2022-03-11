#!/bin/sh

PIPENV_VERBOSITY=-1 pipenv lock -r > requirements.txt
PIPENV_VERBOSITY=-1 pipenv lock -r --dev > requirements-dev.txt
