RATIO Tool
======

A tool to add knowledge to a rdf knowledgebase.


Install
-------

    # clone the repository
    $ git clone https://github.com/ArneKramerSunderbrink/ratio
    $ cd ratio

Create a virtualenv and activate it:

    $ python3 -m venv venv
    $ . venv/bin/activate

Install Ratio:

    $ pip install -e .


Run
---

    $ export FLASK_APP=ratio
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run

Open http://127.0.0.1:5000 in a browser.

If you want to populate the database with dummy data to test the tool (including a user called 'test' with password 'test'), call:

    $ flask db-add-dummy


Test
----

    $ pip install '.[test]'
    $ pytest

Run with coverage report:

    $ coverage run -m pytest
    $ coverage report
    $ coverage html  # open htmlcov/index.html in a browser


Deploy with Gunicorn
----

Build distribution file:

    $ pip install wheel
    $ python3 setup.py bdist_wheel

Copy the distribution file from `dist/` as well as `deploy/deploy.sh` and `deploy/gunicorn_conf.py` to a folder on your server.
Adapt the deploy script to you environment, especially the secret key and the url prefix.
Comment out `flask db-add-dummy` if no dummy data is needed.
Call:

    $ chmod +x deploy.sh
    $ source deploy.sh
    
Run the app with:

    $ gunicorn --config ./gunicorn_conf.py --daemon "ratio:create_app()"

Stop all(!) gunicorn process with:

    $ pkill gunicorn