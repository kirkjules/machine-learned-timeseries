import copy
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
from tqdm import tqdm
from loguru import logger
from htp.api import oanda
from htp.toolbox import dates, workshop
from htp.analyse import evaluate, indicator

logger.enable("htp.api.oanda")


def setup(func, instrument, queryParameters):
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

    queryParameters_copy = copy.deepcopy(queryParameters)
    date_gen = dates.Select(
        from_=queryParameters_copy["from"], to=queryParameters_copy["to"],
        local_tz="America/New_York").by_month()
    date_list = []
    for i in date_gen:
        queryParameters_copy["from"] = i["from"]
        queryParameters_copy["to"] = i["to"]
        date_list.append(copy.deepcopy(queryParameters_copy))
    data_query = workshop.ParallelWorker(
        func, "queryParameters", iterable=date_list, instrument=instrument
        ).prl()
    data_concat = pd.concat(data_query)
    data_clean = data_concat[~data_concat.index.duplicated()]
    data = data_clean.sort_index()
    data.name = "{}".format(queryParameters_copy["price"])
    return data.astype("float")


def main():

    # DATA --> object: data_temp
    func = oanda.Candles.to_df
    instrument = "AUD_JPY"
    queryParameters = {
        "from": "2008-06-01 17:00:00", "to": "2019-08-20 17:00:00",
        "granularity": "H1", "price": "M"}

    data_mid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("data_mid", data_mid)

    queryParameters["price"] = "A"
    data_ask = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("data_ask", data_ask)

    queryParameters["price"] = "B"
    data_bid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("data_bid", data_bid)

    # periods = list(range(3, 101, 1))
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in tqdm(periods):
        avg = indicator.smooth_moving_average(
            data_mid, column="close", period=i)
        avgs.append(avg)
    sma_x_y = pd.concat(avgs, axis=1)
    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("sma_x_y", sma_x_y)

    # PROPERTIES --> object: data_temp
    iky = indicator.ichimoku_kinko_hyo(data_mid)
    iky_close = pd.concat([iky[["tenkan", "kijun", "senkou_A", "senkou_B"]],
                           data_mid["close"]], axis=1)
    iky_close["iky_cat"] = iky_close.apply(evaluate.iky_cat, axis=1)

    rsi = indicator.relative_strength_index(data_mid)

    stoch = indicator.stochastic(data_mid)
    stoch["stoch_diff"] = stoch["%K"] - stoch["%D"]

    macd = indicator.moving_average_convergence_divergence(data_mid)

    adx = indicator.Momentum.average_directional_movement(data_mid)

    atr = indicator.Momentum.average_true_range(data_mid)

    data_properties = pd.concat(
        [iky_close["iky_cat"], rsi["RSI"], adx["ADX"],
         stoch[["%K", "%D", "stoch_diff"]], atr["ATR"],
         macd[["MACD", "Signal", "Histogram"]]], axis=1)

    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("properties", data_properties)

    # to-do
    sma_close = pd.concat(
        [data_mid["close"], data_properties["ATR"], sma_x_y], axis=1)
    sma_close["close_diff"] = sma_close["close"] - sma_close["close"].shift(1)
    sma_close["close_diff_v_atr"] = np.where(
        sma_close["close_diff"].abs() > sma_close["ATR"], 1, 0)
    for i in sma_x_y.columns:
        sma_close[f"{i}_close_diff%"] =\
                (sma_close["close"] - sma_close[i]) /\
                sma_close["close"] *\
                100
        sma_close.drop(i, axis=1, inplace=True)
    sma_close.drop(["close", "ATR", "close_diff"], axis=1, inplace=True)
    sma_close = sma_close.round(4)


if __name__ == "__main__":
    main()
