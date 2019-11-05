from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint('home', __name__)

@bp.route('/index')
@login_required
def index():
    return render_template('base.html', title='Home')
