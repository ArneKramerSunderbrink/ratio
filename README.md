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

Or on Windows cmd:

    $ py -3 -m venv venv
    $ venv\Scripts\activate.bat

Install Ratio:

    $ pip install -e .


Run
---

    $ export FLASK_APP=ratio
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run

Or on Windows cmd:

    > set FLASK_APP=raio
    > set FLASK_ENV=development
    > flask init-db
    > flask run

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