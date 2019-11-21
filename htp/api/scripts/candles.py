import click
from uuid import uuid4, UUID
from celery import chord
from copy import deepcopy
from htp.aux import tasks, models
from htp.aux.database import db_session
from htp.toolbox import dates


def arg_prep(queryParameters):

    qPcopy = deepcopy(queryParameters)
    date_gen = dates.Select(
        from_=qPcopy["from"],  # .strftime("%Y-%m-%d %H:%M:%S"),
        to=qPcopy["to"],  # .strftime("%Y-%m-%d %H:%M:%S"),
        local_tz="America/New_York").by_month()

    date_list = []
    for i in date_gen:
        qPcopy["from"] = i["from"]
        qPcopy["to"] = i["to"]
        date_list.append(deepcopy(qPcopy))

    return date_list


def get_data(ticker, price, granularity, from_, to, smooth, db=True):

    args = {"price": price,
            "granularity": granularity,
            "from": from_,
            "to": to,
            "smooth": smooth}

    _id = None
    if db:
        _id = uuid4()
        db_session.add(
            models.getTickerTask(
                id=_id, ticker=ticker, price=price, granularity=granularity
            )
        )

    param_set = arg_prep(args)
    header = []
    for params in param_set:
        g = tasks.session_get_data.signature(
            (ticker,), {"params": params, "timeout": 30, "db": db})
        g.freeze()
        print(g.id)
        header.append(g)
        if db:
            db_session.add(
                models.subTickerTask(
                    id=UUID(g.id), get_id=_id, _from=params["from"],
                    to=params["to"]
                )
            )

    if db:
        db_session.commit()

    callback = tasks.merge_data.signature(
        (price, granularity, ticker), {"task_id": _id})
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
