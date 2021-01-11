#!/usr/bin/env bash
set -e

# create virtual environment
python3 -m venv venv
source venv/bin/activate

# install modules for deployment and the tool
pip install meinheld gunicorn ratio-0.1-py2.py3-none-any.whl

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
# Prepends URL_PREFIX to all routes (including static etc.), comment or set to '' if you don't want any
echo "URL_PREFIX = '/ratio'" >> venv/var/ratio-instance/config.py
# Do logging via gunicorn and with the gunicorn level
echo "GUNICORN_LOGGER = True" >> venv/var/ratio-instance/config.py
# Configure frontend
echo "FRONTEND_CONFIG=dict(
    Subgraph_term='Clinical trial',
    subgraph_term='clinical trial',
    color1='#E6F7FF',
    color2='#F3F3DB',
    font_color1='#000000',
    font_color2='#000000'
)" >> venv/var/ratio-instance/config.py

touch log.txt