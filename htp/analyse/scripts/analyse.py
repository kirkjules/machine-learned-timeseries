"""A command line script to generate indicator values from select ticker data.
"""
# import os
import click
# from celery import group
from htp.aux import tasks
from htp.aux.database import db_session
from htp.analyse.indicator import ichimoku_kinko_hyo, momentum, stochastic,\
        moving_average_convergence_divergence, relative_strength_index
from htp.aux.models import getTickerTask, indicatorTask, moving_average,\
        ichimoku, convergence_divergence, relative_strength
from htp.aux.models import stochastic as table_stoch
from htp.aux.models import momentum as table_momentum


d = {ichimoku_kinko_hyo: (ichimoku, ('ichimoku_status',)),
     stochastic: (table_stoch, ('stochastic_status',)),
     relative_strength_index: (relative_strength, ('rsi_status',)),
     moving_average_convergence_divergence: (
         convergence_divergence, ('macd_status',)),
     momentum: (table_momentum, ('atr_status', 'adx_status'))}


def get_data(ticker, granularity, target=None):
    """Function that enqueues indicator calculations in celery to be actioned
    by a rabbitmq backend."""

    _id = None
    shift = -1
    entry = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.price == 'M',
        getTickerTask.granularity == granularity).first()
    if target:
        entry_target = db_session.query(getTickerTask).filter(
            getTickerTask.ticker == ticker, getTickerTask.price == 'M',
            getTickerTask.granularity == target).first()
        _id = entry_target.id
        shift = -4
    task_id = entry.id
    indicator = db_session.query(indicatorTask).get(task_id)
    if indicator is None:
        db_session.add(indicatorTask(get_id=task_id))
    else:
        for i in ['adx_status', 'atr_status', 'stochastic_status',
                  'rsi_status', 'macd_status', 'ichimoku_status', 'sma_status',
                  'status']:
            setattr(indicator, i, 0)
        for table in [moving_average, ichimoku, convergence_divergence,
                      table_momentum, relative_strength, table_stoch]:
            db_session.query(table).filter(table.batch_id == entry.id).delete(
                synchronize_session=False)
        db_session.commit()

    tasks.set_smooth_moving_average.delay(task_id)

    for f in d.keys():
        tasks.set_indicator.delay(
            task_id, f, d[f][0], d[f][1], target=_id, shift=shift)

    return None


@click.command()
@click.argument("ticker", type=click.STRING)
@click.argument("price", type=click.STRING)
@click.argument("granularity", type=click.STRING)
def clickIndicator(ticker, price, granularity):
    return get_data(ticker, granularity)


if __name__ == '__main__':
    clickIndicator()
