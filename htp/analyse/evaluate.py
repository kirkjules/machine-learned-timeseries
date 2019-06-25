"""Module used to evaluate trade signals generated from analysis."""
import numpy as np
import pandas as pd


def entry_exit_combine(df, entry, exit):
    """
    A functin to combine entry and exit timestamps for trades generated via
    signal cross logic.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe that contains the trade signals with respective entry and
        exit columns.
    entry : str
        The label for the column containing entry timestamps.
    exit : str
        The label for the column containing exit timestamps.

    Returns
    -------
    pandas.DataFrame
        Dataframe will contain two columns, designated "entry" and "exit"
        respectively. Each row is one trade.
    """
    en = df.entry[df[entry] == True].reset_index()
    en = en.drop("entry", axis=1).rename(columns={"index": "entry"})
    ex = df.exit[df[exit] == True].reset_index()
    ex = ex.drop("exit", axis=1).rename(columns={"index": "exit"})

    if ex.loc[0][0] < en.loc[0][0]:
        ex_clean = ex.drop([0], inplace=False)
        del ex
        ex = ex_clean.reset_index(drop=True, inplace=False)

    out = pd.concat([en, ex], axis=1)
    trade = out[~out["exit"].isnull()]
    return trade


def buy_signal_cross(df, fast, slow):
    """
    A function to identify trades based off two signals crossing one another.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe that contains two signals in their respective columns.
    fast : str
        The column label that corresponds to the fast, more responsive, signal,
        e.g. the smaller period moving average.
    slow : str
        The column label that corresponds to the slow, less responsive, signal,
        e.g. the larger period moving average.

    Results
    -------
    pandas.DataFrame
        A pandas dataframe that will contain two columns containing the entry
        and exit timestamps respectively for a trade.
    """
    system = "{} > {}".format(fast, slow)
    signal = df.apply(
        lambda x: x[fast] > x[slow], axis=1).rename(system).to_frame()
    signal["prev"] = signal[system].shift(2)
    signal["curr"] = signal[system].shift(1)
    signal["entry"] = signal.apply(
        lambda x: x["prev"] is False and x["curr"] is True, axis=1)
    signal["exit"] = signal.apply(
        lambda x: x["prev"] is True and x["curr"] is False, axis=1)
    trade = entry_exit_combine(signal, "entry", "exit")
    return trade


def sell_signal_cross(df, fast, slow):
    pass


if __name__ == "__main__":

    from htp.api import oanda
    from htp.analyse import indicator
    ticker = "AUD_JPY"
    arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                 "granularity": "D",
                 "smooth": True,
                 "count": 50}
    data = oanda.Candles.to_df(instrument=ticker, queryParameters=arguments)
    data_index_dt = data.set_index(
        pd.to_datetime(data.index,
                       format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
    data_sorted = data_index_dt.sort_index()
    sma_5 = indicator.smooth_moving_average(
        data_sorted, column="close", period=5)
    sma_5_10 = indicator.smooth_moving_average(
        data_sorted, df2=sma_5, column="close", concat=True, period=10)
    entry_exit = buy_signal_cross(sma_5_10, "close_sma_5", "close_sma_10")
    print(entry_exit)
