# call for participants

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for

bp = Blueprint('call', __name__, url_prefix='/call')


@bp.route('')
def call():
    return redirect(url_for('call.call_de'))


@bp.route('en')
def call_en():
    return render_template('call_en.html')


@bp.route('de')
def call_de():
    return render_template('call_de.html')
