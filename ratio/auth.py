from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from functools import wraps
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from ratio.db import get_db

bp = Blueprint('auth', __name__)


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next_url=request.full_path))

        return view(*args, **kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
        )


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a registered user by adding the user id to the session."""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session['user_id'] = user['id']
            next_url = request.args.get('next_url', '', type=str)
            if next_url:
                print(next_url)
                return redirect(request.script_root + next_url)
            else:
                return redirect(url_for('tool.index'))

        flash(error)

    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for('auth.login'))


def subgraph_access(user_id, subgraph_id):
    access = get_db().execute(
        'SELECT EXISTS ('
        ' SELECT 1 FROM access JOIN subgraph ON subgraph_id = id WHERE user_id = ? AND subgraph_id = ? AND deleted = 0'
        ')',
        (user_id, subgraph_id)
    ).fetchone()[0]
    return bool(access)
