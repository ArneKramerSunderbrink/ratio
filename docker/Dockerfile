FROM python:3.6

COPY ratio-1.0.0-py2.py3-none-any.whl ratio-1.0.0-py2.py3-none-any.whl
COPY wsgi.py wsgi.py
COPY gunicorn_conf.py gunicorn_conf.py

RUN pip install meinheld gunicorn ratio-1.0.0-py2.py3-none-any.whl

RUN export FLASK_APP=ratio
RUN flask init-db
RUN flask db-add-dummy

CMD gunicorn -k egg:meinheld#gunicorn_worker -c "./gunicorn_conf.py" wsgi:app