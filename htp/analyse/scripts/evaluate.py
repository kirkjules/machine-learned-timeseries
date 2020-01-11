"""A command line script to generate trade signals from select sma crosses
calculated from given ticker data."""
from uuid import uuid4
from celery import group
from htp.aux import tasks
from htp.aux.database import db_session
from htp.aux.models import getTickerTask, genSignalTask


def get_data(ticker, granularity, system, db=True):
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
    db : boolean
        Flag to enable db recording.
    """

    batch_id = None
    if db:
        entry = db_session.query(getTickerTask).filter(
            getTickerTask.ticker == ticker, getTickerTask.price == 'M',
            getTickerTask.granularity == f'{granularity.split(" ")[0]}'
        ).first()
        if entry is None:
            # Indirect check to confirm pre-existing ticker data.
            return f"No data has been stored for {ticker} in {granularity} \
intervals."
        batch_id = entry.id
        ids = {}
        for k in system:
            ids[k] = {}
            for trade in ['buy', 'sell']:
                ids[k][trade] = uuid4()
                db_session.add(
                    genSignalTask(
                        id=ids[k][trade],
                        batch_id=batch_id,
                        sma_close_x=k.split(' ')[0],
                        sma_close_y=k.split(' ')[1],
                        trade_direction=trade,
                        exit_strategy="trailing_atr_6"))
        db_session.commit()

    files = []
    base = f'/Users/juleskirk/Documents/projects/htp/data/{ticker}/'
    g = f'{granularity.split(" ")[0]}/'
    # granularity = 'M15 H1' OR 'H1 H4' OR 'H4 None'

    for P in ['M', 'B', 'A']:
        df = base + g + 'price.h5'
        files.append((df, f'{P}', P))

    files.append((base + g + 'indicators.h5', 'I', 'target'))

    sup_indicators = base + f'{granularity.split(" ")[1]}/indicators.h5'
    if granularity.split(" ")[1] != 'None':
        files.append((sup_indicators, 'I', 'sup'))

    load = tasks.load_signal_data.s(files)
    # return load.delay()

    s = []
    for k in system:
        for trade in ['buy', 'sell']:
            s.append(tasks.gen_signals.s(
                k.split(' ')[0], k.split(' ')[1], trade, ticker,
                granularity.split(" ")[0], 6, task_id=ids[k][trade]))
    gen = group(s)

    return (load | gen).delay()
