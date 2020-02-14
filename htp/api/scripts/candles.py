import click
from celery import chord
from copy import deepcopy
from uuid import uuid4  # , UUID
from htp.toolbox import dates
from htp.aux import tasks
from datetime import datetime
from htp.aux.database import db_session
from htp.aux.models import GetTickerTask, SubTickerTask, Candles, Indicators,\
    IndicatorTask


# imported celery app for chord to recognise backend.
# unsure if this is required in production code, was working fine earlier.
# from htp import celery
# print(celery.conf.result_backend)


def arg_prep(queryParameters):

    qPcopy = deepcopy(queryParameters)
    date_gen = dates.Select(
        from_=qPcopy["from"].strftime("%Y-%m-%d %H:%M:%S"),
        to=qPcopy["to"].strftime("%Y-%m-%d %H:%M:%S"),
        local_tz="America/New_York").by_month()

    date_list = []
    for i in date_gen:
        qPcopy["from"] = i["from"]
        qPcopy["to"] = i["to"]
        date_list.append(deepcopy(qPcopy))

    return date_list


def get_data(ticker, price, granularity, from_, to, smooth):
    """Function to initiate ticker data download and entry logging in a
    database.

    Parameters
    ----------
    ticker : str
       The target instrument to be queried using the preset function for a
       given endpoint.
    price : str
       The candle type for which ticker data should be sourced.
    granularity : str
       The time interval the define the period which defines the timeseries
       data.
    from_ : datetime.datetime
       The startpoint from which data should be downloaded.
    to : datetime.datetime
       The endpoint to which data should be downloaded.
    smooth : bool
       A flag that the api endpoint accepts to ensure the close and open
       values for adjacent candles match.

    Returns
    -------
      None

    Notes
    -----
    - If the data download is successfull the timeseries will be saved as in
    the 'candles' table in the database, with a foreign key on each row
    relating the given entry the initial get ticker query to defines the ticker
    type, price, granularity, and batch from and to date.
    - The database logging functionality is designed to recylce pre-existing
    rows that match the same ticker, price and granularity criteris, updating
    the from_ and to values accordingly.
    """
    for val in price:
        for interval in granularity:

            args = {"price": val, "granularity": interval, "from": from_,
                    "to": to, "smooth": smooth}

            entry = db_session.query(GetTickerTask).filter(
                GetTickerTask.ticker == ticker, GetTickerTask.price == val,
                GetTickerTask.granularity == interval).first()
            if entry is None:
                batch_id = uuid4()
                db_session.add(GetTickerTask(
                    id=batch_id, ticker=ticker, price=val, _from=from_, to=to,
                    granularity=interval))
            else:
                batch_id = entry.id
                setattr(entry, "_from", from_)
                setattr(entry, "to", to)
                for table in [SubTickerTask, Candles, IndicatorTask,
                              Indicators]:
                    db_session.query(table).filter(table.batch_id == entry.id)\
                        .delete(synchronize_session=False)

            header = []
            param_set = arg_prep(args)
            for params in param_set:
                g = tasks.session_get_data.signature(
                    (ticker,), {"params": params, "timeout": 30})
                g.freeze()
                # print(g.id)
                header.append(g)
                db_session.add(SubTickerTask(  # id=UUID(g.id),
                    batch_id=batch_id,
                    _from=datetime.strptime(
                        params["from"], '%Y-%m-%dT%H:%M:%S.%f000Z'),
                    to=datetime.strptime(
                        params["from"], '%Y-%m-%dT%H:%M:%S.%f000Z')))

            callback = tasks.merge_data.s(
                ticker, price, granularity, task_id=batch_id)
            chord(header)(callback)

    db_session.commit()


@click.command()
@click.argument("ticker", type=click.STRING)
@click.option("--price", default="M", type=click.STRING)
@click.option("--granularity", default="M15", type=click.STRING)
@click.option(
    "--from", "-f", "from_", default=None, type=click.DateTime(formats=None))
@click.option("--to", default=None, type=click.DateTime(formats=None))
@click.option("--smooth", default=False, type=click.BOOL)
def cli_get_data(ticker, price, granularity, from_, to, smooth):
    return get_data(ticker, price, granularity, from_, to, smooth).get()


if __name__ == "__main__":
    cli_get_data()
