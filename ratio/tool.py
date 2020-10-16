from flask import Blueprint
from flask import g
from flask import render_template
from flask import get_template_attribute
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort
from sqlite3 import IntegrityError

from ratio.auth import login_required
from ratio.db import get_db

bp = Blueprint('tool', __name__)


@bp.route('/')
@bp.route('/<int:subgraph_id>')
@login_required
def index(subgraph_id=None):
    """Show all the posts, most recent first.""" #todo docu machen
    user_id = g.user['id']
    db = get_db()

    # for the subgraph menu
    subgraph_list = db.execute(
        'SELECT id, name, finished'
        ' FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE user_id = ?'
        ' ORDER BY name ASC',
        (user_id,)
    ).fetchall()

    if subgraph_id is None:
        subgraph = {'id': 0, 'name': '', 'finished': False}
        return render_template('tool/index.html', subgraph=subgraph, subgraph_list=subgraph_list)

    # todo testen ob dem user der subgraph gehört (gen function schreiben) abort(403)

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        abort(404)

    knowledge = db.execute(
        'SELECT * FROM knowledge WHERE subgraph_id = ?', (subgraph_id,)
    )

    return render_template('tool/index.html', subgraph=subgraph, knowledge=knowledge, subgraph_list=subgraph_list)


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


@login_required
@bp.route('/_add_subgraph')
def add_subgraph():
    user_id = g.user['id']
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='Subgraph name cannot be empty.')

    db = get_db()
    try:
        db.execute(
            'INSERT INTO subgraph (name, finished) VALUES (?, ?)',
            (subgraph_name, False)
        )
    except IntegrityError:
        return jsonify(error='A subgraph of that name already exists.')

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE name = ?', (subgraph_name,)
    ).fetchone()

    db.execute(
        'INSERT INTO access (user_id, subgraph_id) VALUES (?, ?)',
        (user_id, subgraph['id'])
    )

    db.commit()
    return jsonify(redirect=url_for("tool.index", subgraph_id=subgraph['id']))


@login_required
@bp.route('/_add_knowledge')
def add_knowledge():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    rdf_subject = request.args.get('subject', '', type=str)
    rdf_predicate = request.args.get('predicate', '', type=str)
    rdf_object = request.args.get('object', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not rdf_subject or rdf_subject.isspace():
        return jsonify(error='Subject cannot be empty.')
    if not rdf_predicate or rdf_predicate.isspace():
        return jsonify(error='Predicate cannot be empty.')
    if not rdf_object or rdf_object.isspace():
        return jsonify(error='Object cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    subgraph_exists = db_cursor.execute(
        'SELECT EXISTS (SELECT 1 FROM subgraph WHERE id = ?)', (subgraph_id,)
    )

    if not subgraph_exists:
        return jsonify(error='Subgraph with id {} does not exist.'.format(subgraph_id))

    # todo check if user has access to subgraph

    db_cursor.execute(
        'INSERT INTO knowledge (subgraph_id, author_id, subject, predicate, object) VALUES (?, ?, ?, ?, ?)',
        (subgraph_id, user_id, rdf_subject, rdf_predicate, rdf_object)
    )
    knowledge_id = db_cursor.lastrowid

    db.commit()

    render_knowledge_row = get_template_attribute('tool/macros.html', 'knowledge_row')
    knowledge_row = render_knowledge_row(knowledge_id, subgraph_id, rdf_subject, rdf_predicate, rdf_object)

    return jsonify(knowledge_id=knowledge_id, subject=rdf_subject, predicate=rdf_predicate, object=rdf_object,
                   knowledge_row=knowledge_row)
