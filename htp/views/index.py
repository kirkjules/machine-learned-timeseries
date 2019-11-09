from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint('index', __name__)


@bp.route('/')
@login_required
def monitor():
    return render_template('base.html')
