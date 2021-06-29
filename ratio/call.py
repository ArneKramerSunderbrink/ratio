# call for participants

from flask import Blueprint
from flask import render_template

bp = Blueprint('call', __name__, url_prefix='/call')


@bp.route('')
def call():
    return render_template('call.html')
