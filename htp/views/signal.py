from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from htp.aux.forms import SignalForm
from htp.analyse.scripts.evaluate import get_data


bp = Blueprint('signal', __name__)


@bp.route('/signal', methods=('GET', 'POST'))
@login_required
def signals():

    form = SignalForm()
    if form.validate_on_submit():
        print(form.select_all.data)
        print(form.system.data)
        for interval in form.granularity.data:
            get_data(
                form.ticker.data, interval, form.system.data, db=False)
        return redirect(url_for('index.monitor'))

    return render_template('signal.html', form=form)
