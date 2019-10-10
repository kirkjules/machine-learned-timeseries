"""A command line script to query ticker data directly from the oanda api.

E.g. candles "AUD_JPY" --granularity "H1" --from "2014-04-03 22:00:00" --to
"2018-04-03 22:00:00" --background True"""
import os
import copy
import click
import pandas as pd
from loguru import logger
from htp.api.oanda import Candles
from htp.toolbox import dates, engine

logger.enable("htp.api.oanda")


def fmt(date):
    if date is not None:
        # str_ = date.strftime("%Y-%m-%dT%H:%M:%S.%f000Z")
        str_ = date.strftime("%Y-%m-%d %H:%M:%S")
        return str_


def arg_prep(queryParameters):

    queryParameters_copy = copy.deepcopy(queryParameters)
    date_gen = dates.Select(
        from_=queryParameters_copy["from"], to=queryParameters_copy["to"],
        local_tz="America/New_York").by_month()
    date_list = []

    for i in date_gen:
        queryParameters_copy["from"] = i["from"]
        queryParameters_copy["to"] = i["to"]
        date_list.append(copy.deepcopy(queryParameters_copy))

    return date_list


def block_acquire(func, instrument, queryParameters, sync=False):
    """
    Wrapper function that groups arguments parsing, data querying and data
    clean up.

    Parameters
    ----------
    func : {"oanda.Candles.to_json", "oanda.Candles.to_df"}
        The function that should be used to query the ticker data.

    instrument : str
        The ticker instrument whose timeseries should be queried.

    queryParameters : dict
        Variables that will be parsed in the request body onto the api
        endpoint.

    Returns
    -------
    pandas.core.frame.DataFrame
        The timeseries ticker data stored in a pandas DataFrame and sorted by
        datetime index.

    Notes
    -----
    Flow
    1. State date/time range with datetime strings listed in ISO-8601 format.
    2. Convert date/time to UTC.
    Note: Parse to query in RFC3339 format: "YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ"
    3. State granularity
    Note: daily candles should keep default setting for dailyAlignment and
            alignmentTimezone settings. Smooth must be set to True to ensure
            same values as displayed by Oanda on the online portal.
    4. Query data.
    Note: any actions logged will be in UTC time. If the user needs a timestamp
            displayed in local time this functionality will be applied in the
            relevant functions and methods.

    Examples
    --------
    >>> func = oanda.Candles.to_df
    >>> instrument = "AUD_JPY"
    >>> queryParameters = {
    ...    "from": "2012-01-01 17:00:00", "to": "2012-06-27 17:00:00",
    ...    "granularity": "H1", "price": "M"}
    >>> data_mid = setup(
    ...    func=func, instrument=instrument, queryParameters=queryParameters)
    >>> data_mid.head()
                           open    high     low   close
    2012-01-01 22:00:00  78.667  78.892  78.627  78.830
    2012-01-01 23:00:00  78.824  78.879  78.751  78.768
    2012-01-02 00:00:00  78.776  78.839  78.746  78.803
    2012-01-02 01:00:00  78.807  78.865  78.746  78.790
    2012-01-02 02:00:00  78.787  78.799  78.703  78.733
    """
    date_list = arg_prep(queryParameters)

    if not sync:
        data_query = engine.Parallel.worker(
            func, "queryParameters", iterable=date_list, instrument=instrument)
    else:
        data_query = engine.Worker.sync(
            func, "queryParameters", iterable=date_list, instrument=instrument)

    data_concat = pd.concat(data_query)
    data_clean = data_concat[~data_concat.index.duplicated()]
    data = data_clean.sort_index()
    data.name = "{}".format(queryParameters["price"])
    return data.astype("float")


def background_acquire(func, instrument, queryParameters):

    files = {}
    for i in arg_prep(queryParameters):
        filename = f"data/{instrument}-{i['from']}-{i['to']}.csv".replace(
            ":", "-").replace(".000000000Z", "")
        print(filename)
        job = engine.launch_task(
            Candles.to_df, instrument=instrument, queryParameters=i,
            filename=filename)
        files[job] = filename

    if engine.queue_completed(files.keys()):
        data_query = []
        for j in files.keys():
            data_query.append(
                pd.read_csv(
                    files[j], index_col=0, parse_dates=True,
                    infer_datetime_format=True))
            os.remove(files[j])

        data_concat = pd.concat(data_query)
        data_clean = data_concat[~data_concat.index.duplicated()]
        data = data_clean.sort_index()
        data.name = "{}".format(queryParameters["price"])
        return data.astype("float")


# @click.argument("filename", type=click.STRING) to be auto-generated.

@click.command()
@click.argument("ticker", type=click.STRING)
@click.option("--sync", default=True, type=click.BOOL)
@click.option("--background", default=False, type=click.BOOL)
@click.option("--price",
              default="M",
              type=click.STRING,
              help="The Price components to get candlestick data for.\
              Can contain any combination of the characters M midpoint\
              candles B bid candles and A ask candles")
@click.option("--granularity",
              default="S5",
              type=click.STRING,
              help="The granularity of the candlesticks to fetch")
@click.option("--count",
              default="500",
              type=click.IntRange(1, 5000, clamp=True),
              help="The number of candlesticks to return in the reponse.\
              Count should not be specified if both the start and end\
              parameters are provided, as the time range combined with the\
              granularity will determine the number of candlesticks to\
              return.")
@click.option("--from", "-f", "from_",
              default=None,
              type=click.DateTime(formats=None),
              help="The start of the time range to fetch candlesticks for.")
@click.option("--to",
              default=None,
              type=click.DateTime(formats=None),
              help="The end of the time range to fetch candlesticks for.")
@click.option("--smooth",
              default=False,
              type=click.BOOL,
              help="A flag that controls whether the candlestick is\
              “smoothed” or not. A smoothed candlestick uses the previous\
              candle’s close price as its open price, while an unsmoothed\
              candlestick uses the first price from its time range as its\
              open price.")
@click.option("--includefirst",
              default=True,
              type=click.BOOL,
              help="A flag that controls whether the candlestick that is\
              covered by the from time should be included in the results.\
              This flag enables clients to use the timestamp of the last\
              completed candlestick received to poll for future candlesticks\
              but avoid receiving the previous candlestick repeatedly.")
@click.option("--dailyalignment",
              default=17,
              type=click.IntRange(0, 23, clamp=True),
              help="The hour of the day (in the specified timezone) to use\
              for granularities that have daily alignments.")
@click.option("--weeklyalignment",
              default="Friday",
              type=click.STRING,
              help="The day of the week used for granularities that have\
              weekly alignment.")
@click.option("--alignmenttimezone",
              default="America/New_York",
              type=click.STRING,
              help="The timezone to use for the dailyAlignment parameter.\
              Candlesticks with daily alignment will be aligned to the\
              dailyAlignment hour within the alignmentTimezone. Note that\
              the returned times will still be represented in UTC.")
def clickData(ticker, sync, price, granularity, count, from_, to, smooth,
              includefirst, dailyalignment, weeklyalignment, background,
              alignmenttimezone):

    arguments = {"price": price,
                 "granularity": granularity,
                 "count": count,
                 "from": fmt(from_),
                 "to": fmt(to),
                 "smooth": smooth,
                 "includeFirst": includefirst,
                 "dailyAlignment": dailyalignment,
                 "alignmentTimezone": alignmenttimezone,
                 "weeklyAlignment": weeklyalignment}

    if background:  # to overwrite sync argument and prevent logic conflict.
        sync = False

    if arguments["to"] is None and arguments["from"] is None:
        del arguments["to"]
        del arguments["from"]
    elif arguments["to"] is not None and arguments["from"] is None:
        del arguments["from"]
    elif arguments["to"] is None and arguments["from"] is not None:
        del arguments["to"]
    else:
        del arguments["count"]

    if sync and "count" not in arguments.keys():  # for-loop
        candle_data = block_acquire(
            func=Candles.to_df, instrument=ticker, queryParameters=arguments,
            sync=True)
    elif not sync and not background and "count" not in arguments.keys():
        # multiprocessing-parallel
        candle_data = block_acquire(
            func=Candles.to_df, instrument=ticker, queryParameters=arguments)
    elif background and "count" not in arguments.keys():
        # background-job
        candle_data = background_acquire(
            func=Candles.to_df, instrument=ticker, queryParameters=arguments)
    elif "count" in arguments.keys():  # single api call
        candle_data = Candles.to_df(
            **{"instrument": ticker, "queryParameters": arguments})

    with pd.HDFStore(f"data/{ticker}-{granularity}.h5") as store:
        store.append(f"{price}", candle_data)

    click.echo("Download complete.")
