#!/usr/bin/env bash
set -e

# create virtual environment
python3 -m venv venv
source venv/bin/activate

# install modules for deployment and the tool
pip install meinheld gunicorn ratio-1.0.0-py2.py3-none-any.whl

# Tell Flask what app to use
export FLASK_APP=ratio

# Initialize the database
flask init-db

# Fill the database with dummy data
# including a user test with password test
# comment out if you don't need that
flask db-add-dummy

# Secret key used for the session cookie etc.
echo "SECRET_KEY = b'\x99<\xa5\xd5Q\xd5\xc3\xa8\x8b\x11R\xc7\xd54\x93j'" > venv/var/ratio-instance/config.py
# Prepends URL_PREFIX to all routes, comment or set to '' if you don't want any
echo "URL_PREFIX = '/ratio'" >> venv/var/ratio-instance/config.py