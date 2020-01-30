"""A command line script to generate trade signals from select sma crosses
calculated from given ticker data."""
from htp.aux import tasks
from htp.aux.database import db_session
from htp.aux.models import getTickerTask


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
           35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
systems = [f"close_sma_{i} close_sma_{j}" for i in periods for j in periods
           if i < (j - 1)]
parts = list(split(systems, 10))


def get_data(ticker, granularity, system, multiplier):
    """Function that enqueues system signals generators in celery to be managed
    by a rabbitmq broker.

    Parameters
    ----------
    ticker : str
        Target ticker's symbol.
    granularity : str
        Granularity on which to apply signal generator, string includes
        supplementary granularity to call extra properties, delimited by a
        space.
    system : list
        A list of systems with each item defined in the following nomenclature,
        'close_sma_x close_sma_y'
    """
    # removing all checks, will implement later.
    mid = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.price == 'M',
        getTickerTask.granularity == granularity).first()
    ask = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.price == 'A',
        getTickerTask.granularity == granularity).first()
    bid = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.price == 'B',
        getTickerTask.granularity == granularity).first()

    comb = []
    if system[0] != 'close_sma_3 close_sma_5':
        for s in system:
            comb += parts[1 - int(s)]
    else:
        comb = system

    # print(comb)
    for s in comb:
        for trade in ['buy', 'sell']:
            tasks.gen_signals.delay(
                mid.id, ask.id, bid.id, s.split(' ')[0], s.split(' ')[1],
                trade, multiplier=int(multiplier))
