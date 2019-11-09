from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from htp.aux.forms import CandlesForm
from htp.api.scripts.candles import get_data


bp = Blueprint('get', __name__)


@bp.route('/get', methods=('GET', 'POST'))
@login_required
def candles():

    form = CandlesForm()
    if form.validate_on_submit():
        get_data(
            form.ticker.data, form.price.data, form.granularity.data,
            form.from_.data, form.to.data, form.smooth.data)
        return redirect(url_for('index.monitor'))

    return render_template('get.html', form=form)
