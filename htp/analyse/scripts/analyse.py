"""A command line script to generate indicator values from select ticker data.
"""
import os
import click
from celery import group
from htp.aux import tasks
from htp.aux.database import db_session
from htp.aux.models import getTickerTask, indicatorTask


def get_data(ticker, granularity, db=True):
    """Function that enqueues indicator calculations in celery to be actioned
    by a rabbitmq backend."""

    path = f"/Users/juleskirk/Documents/projects/htp/data/{ticker}/\
{granularity}/"
    name = "price.h5"
    key = "/M"

    task_id = None
    if db:
        entry = db_session.query(getTickerTask).filter(
            getTickerTask.ticker == ticker, getTickerTask.price == 'M',
            getTickerTask.granularity == granularity).first()
        if entry is None:
            # Indirect check to confirm pre-existing ticker data.
            return f"No data has been stored for {ticker} in {granularity} \
intervals."
        task_id = entry.id
        indicator = db_session.query(indicatorTask).get(task_id)
        if indicator is None:
            db_session.add(indicatorTask(get_id=task_id))
        else:
            for i in ['adx_status', 'atr_status', 'stochastic_status',
                      'rsi_status', 'macd_status', 'ichimoku_status',
                      'sma_status', 'status']:
                setattr(indicator, i, 0)
        db_session.commit()

    get = tasks.load_data.s(path + name, key)

    # Bulk indicator generation defines use case, indicators are used to teach
    # machine learning which system signals have the highest probability of
    # success. Intentionally removing data input is unecessary at this step in
    # the test flow.
    path_to_ind = path + "indicators/"
    if not os.path.isdir(path_to_ind):
        os.mkdir(path_to_ind)

    header = group(
        tasks.set_smooth_moving_average.s(path_to_ind, task_id=task_id),
        tasks.set_ichimoku_kinko_hyo.s(path_to_ind, task_id=task_id),
        tasks.set_moving_average_convergence_divergence.s(
            path_to_ind, task_id=task_id),
        tasks.set_stochastic.s(path_to_ind, task_id=task_id),
        tasks.set_relative_strength_index.s(path_to_ind, task_id=task_id),
        tasks.set_momentum.s(path_to_ind, task_id=task_id)
    )

    callback = tasks.assemble.si(path, task_id=task_id)

    return (get | header | callback).delay()


@click.command()
@click.argument("ticker", type=click.STRING)
@click.argument("price", type=click.STRING)
@click.argument("granularity", type=click.STRING)
def clickIndicator(ticker, price, granularity):
    return get_data(ticker, price, granularity, db=False).get()


if __name__ == '__main__':
    clickIndicator()
