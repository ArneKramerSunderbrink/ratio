from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort

from ratio.auth import login_required
from ratio.db import get_db

bp = Blueprint('tool', __name__)


@bp.route('/')
@bp.route('/<int:subgraph_id>')
@login_required
def index(subgraph_id=None):
    """Show all the posts, most recent first.""" #todo docu machen
    if subgraph_id is None:
        # todo: render view with overlay on
        subgraph = {'id': 0, 'name': '', 'finished': False}
        return render_template('tool/index.html', subgraph=subgraph)

    db = get_db()

    # todo testen ob dem user der subgraph gehört (gen function schreiben) abort(403)

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        abort(404)

    return render_template('tool/index.html', subgraph=subgraph)


@login_required
@bp.route('/_set_finished')
def set_finished():
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    finished = request.args.get('finished', '', type=str)

    # todo testen ob es den subgraph gibt abort(404)
    # todo testen ob dem user der subgraph gehört (gen function schreiben) abort(403)

    if finished == 'true' or finished == 'false':
        finished = finished == 'true'
        db = get_db()
        db.execute(
            "UPDATE subgraph SET finished = ? WHERE id = ?", (finished, subgraph_id)
        )
        db.commit()
        return jsonify(finished=finished)
    else:
        abort(404)
