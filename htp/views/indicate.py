from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from htp.aux.forms import IndicateForm
from htp.analyse.scripts.analyse import get_data


bp = Blueprint('indicate', __name__)


@bp.route('/indicate', methods=('GET', 'POST'))
@login_required
def indicators():

    form = IndicateForm()
    if form.validate_on_submit():
        for interval in form.granularity.data:
            if interval == 'H4':
                get_data(form.ticker.data, interval, target='H1')
            elif interval == 'H1':
                get_data(form.ticker.data, interval, target='M15')
            else:
                get_data(form.ticker.data, interval)
        return redirect(url_for('index.monitor'))

    return render_template('indicate.html', form=form)
