import click
from htp import tasks
from celery import chord
from copy import deepcopy
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


def get_data(ticker, price, granularity, from_, to, smooth):

    args = {"price": price,
            "granularity": granularity,
            "from": from_,
            "to": to,
            "smooth": smooth}

    param_set = arg_prep(args)
    header = [tasks.session_get_data.signature(
        (ticker,), {"params": params, "timeout": 30}) for params in param_set]
    callback = tasks.merge_data.s()
    chord(header)(callback)
    # res.get()


@click.command()
@click.argument("ticker", type=click.STRING)
@click.option("--price", default="M", type=click.STRING)
@click.option("--granularity", default="M15", type=click.STRING)
@click.option(
    "--from", "-f", "from_", default=None, type=click.DateTime(formats=None))
@click.option("--to", default=None, type=click.DateTime(formats=None))
@click.option("--smooth", default=False, type=click.BOOL)
def cli_get_data(ticker, price, granularity, from_, to, smooth):
    return get_data(ticker, price, granularity, from_, to, smooth)


if __name__ == "__main__":
    cli_get_data()
