import click
from celery import chord
from copy import deepcopy
from uuid import uuid4, UUID
from htp.toolbox import dates
from htp.aux import tasks
from htp.aux.database import db_session
from htp.aux.models import getTickerTask, subTickerTask, candles


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


def get_data(ticker, price, granularity, from_, to, smooth, db=True):
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
    db : bool
       A flag to ensure the query is logged in the database.

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
    _ids = {}
    header = []
    for val in price:
        for interval in granularity:

            args = {"price": val, "granularity": interval, "from": from_,
                    "to": to, "smooth": smooth}

            _ids[f"{interval}/{val}"] = None
            if db:
                entry = db_session.query(getTickerTask).filter(
                    getTickerTask.ticker == ticker, getTickerTask.price ==
                    val, getTickerTask.granularity == interval).first()
                if entry is None:
                    _ids[f"{interval}/{val}"] = uuid4()
                    db_session.add(getTickerTask(
                        id=_ids[f"{interval}/{val}"], ticker=ticker, price=val,
                        granularity=interval, _from=from_, to=to))
                else:
                    _ids[f"{interval}/{val}"] = entry.id
                    setattr(entry, "_from", from_)
                    setattr(entry, "to", to)
                    db_session.query(subTickerTask).filter(
                        subTickerTask.get_id == entry.id).delete(
                            synchronize_session=False)
                    db_session.query(candles).filter(
                        candles.batch_id == entry.id).delete(
                            synchronize_session=False)

            param_set = arg_prep(args)
            for params in param_set:
                g = tasks.session_get_data.signature(
                    (ticker,), {"params": params, "timeout": 30, "db": db})
                g.freeze()
                # print(g.id)
                header.append(g)
                if db:
                    db_session.add(subTickerTask(
                        id=UUID(g.id), get_id=_ids[f"{interval}/{val}"],
                        _from=params["from"], to=params["to"]))

    if db:
        db_session.commit()

    callback = tasks.merge_data.s(ticker, price, granularity, task_id=_ids)
    return chord(header)(callback)


@click.command()
@click.argument("ticker", type=click.STRING)
@click.option("--price", default="M", type=click.STRING)
@click.option("--granularity", default="M15", type=click.STRING)
@click.option(
    "--from", "-f", "from_", default=None, type=click.DateTime(formats=None))
@click.option("--to", default=None, type=click.DateTime(formats=None))
@click.option("--smooth", default=False, type=click.BOOL)
def cli_get_data(ticker, price, granularity, from_, to, smooth):
    return get_data(
        ticker, price, granularity, from_, to, smooth, db=False).get()


if __name__ == "__main__":
    cli_get_data()
