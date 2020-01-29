from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from htp.aux.forms import SignalForm
from htp.analyse.scripts.predict import get_data


bp = Blueprint('predict', __name__)


@bp.route('/predict', methods=('GET', 'POST'))
@login_required
def signals():

    form = SignalForm()
    if form.validate_on_submit():
        # get_data()
        for interval in form.granularity.data:
            get_data(
                form.ticker.data, interval, form.system.data)
        return redirect(url_for('index.monitor'))

    return render_template('signal.html', form=form)
