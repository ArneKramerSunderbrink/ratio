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


Deploy with Gunicorn and Docker
----

Build distribution file:

    $ pip install wheel
    $ python setup.py bdist_wheel

Copy the distribution file from `dist/` as well as the files from `docker/` to a folder on your server.
Change the secret key in `docker/wsgi.py`.
Call:

    $ docker build -t ratioimage .
    $ docker run --publish 8000:8000 --name --detach ratio ratioimage

Stop with:

    $ docker rm --force ratio