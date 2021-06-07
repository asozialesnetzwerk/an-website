#!/bin/sh

if [ ! -d "venv" ]
then
    # venv doesn't exist, so create it:
    pypy3 -m venv venv
fi

#. venv/bin/activate

exec venv/bin/pypy3 main.py