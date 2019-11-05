from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from htp.forms import CandlesForm
from htp.api.scripts.candles import get_data


bp = Blueprint('acquire', __name__)


@bp.route('/candles', methods=('GET', 'POST'))
@login_required
def acquire():

    form = CandlesForm()
    if form.validate_on_submit():
        print(
            form.ticker.data, form.price.data, form.granularity.data,
            form.from_.data, form.to.data, form.smooth.data)
        get_data(
            form.ticker.data, form.price.data, form.granularity.data,
            form.from_.data, form.to.data, form.smooth.data)
        return redirect(url_for('home.index'))

    return render_template('acquire.html', title='Acquire', form=form)
