"""A command line script to generate indicator values from select ticker data.
"""
# import os
import click
# from celery import group
from htp.aux import tasks
from htp.aux.database import db_session
from htp.aux.models import getTickerTask, indicatorTask, smoothmovingaverage,\
        ichimokukinkohyo, movavgconvdiv, momentum, relativestrengthindex,\
        stochastic


def get_data(ticker, granularity, db=True):
    """Function that enqueues indicator calculations in celery to be actioned
    by a rabbitmq backend."""

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
            for table in [
              smoothmovingaverage, ichimokukinkohyo, movavgconvdiv,
              momentum, relativestrengthindex, stochastic]:
                db_session.query(
                    table).filter(table.batch_id == entry.id).delete(
                        synchronize_session=False)
        db_session.commit()

    tasks.set_smooth_moving_average.delay(task_id)
    tasks.set_ichimoku_kinko_hyo.delay(task_id)
    tasks.set_moving_average_convergence_divergence.delay(task_id)
    tasks.set_momentum.delay(task_id)
    tasks.set_stochastic.delay(task_id)
    tasks.set_relative_strength_index.delay(task_id)

    return None


@click.command()
@click.argument("ticker", type=click.STRING)
@click.argument("price", type=click.STRING)
@click.argument("granularity", type=click.STRING)
def clickIndicator(ticker, price, granularity):
    return get_data(ticker, price, granularity, db=False).get()


if __name__ == '__main__':
    clickIndicator()
