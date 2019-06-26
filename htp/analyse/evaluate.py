"""Module used to evaluate trade signals generated from analysis."""
import numpy as np
import pandas as pd


def entry_exit_combine(df, entry, exit):
    """
    A function to combine entry and exit timestamps for trades generated via
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
    en_prep = df.entry[df[entry] == True].reset_index()
    en = en_prep.drop("entry", axis=1).rename(columns={"index": "entry"})
    ex_prep = df.exit[df[exit] == True].reset_index()
    ex = ex_prep.drop("exit", axis=1).rename(columns={"index": "exit"})

    if ex.loc[0][0] < en.loc[0][0]:
        ex_clean = ex.drop([0], inplace=False)
        del ex
        ex = ex_clean.reset_index(drop=True, inplace=False)

    out = pd.concat([en, ex], axis=1)
    trade = out[~out["exit"].isnull()]
    return trade


def signal_cross(df, fast, slow, trade="buy"):
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
    type : {"buy", "sell"}
        The trade type that should be observed from the signal, i.e. buy or
        sell.

    Results
    -------
    pandas.DataFrame
        A pandas dataframe that will contain two columns containing the entry
        and exit timestamps respectively for a trade.
    
    Examples
    --------
    >>> import pandas as pd
    >>> from pprint import pprint
    >>> from htp.api import oanda
    >>> from htp.analyse import indicator, evaluate
    >>> ticker = "AUD_JPY"
    >>> arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                     "granularity": "D",
                     "smooth": True,
                     "count": 50}
    >>> data = oanda.Candles.to_df(instrument=ticker,
                                   queryParameters=arguments)
    >>> data_index_dt = data.set_index(
            pd.to_datetime(data.index,
                           format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
    >>> data_sorted = data_index_dt.sort_index()
    >>> sma_5 = indicator.smooth_moving_average(data_sorted, column="close",
                                                period=5)
    >>> sma_5_10 = indicator.smooth_moving_average(data_sorted, column="close",
                                                   df2=sma_5, concat=True,
                                                   period=10)
    >>> entry_exit = evaluate.buy_signal_cross(sma_5_10, "close_sma_5",
                                               "close_sma_10")
    >>> pprint(entry_exit.to_dict("index"))
    {0: {'entry': Timestamp('2018-03-11 21:00:00'),
         'exit': Timestamp('2018-03-19 21:00:00')},
     1: {'entry': Timestamp('2018-04-01 21:00:00'),
         'exit': Timestamp('2018-04-02 21:00:00')}}
    """
    if trade == "buy":
        system = "{} > {}".format(fast, slow)
        signal = df.apply(
            lambda x: x[fast] > x[slow], axis=1).rename(system).to_frame()
    elif trade == "sell":
        system = "{} < {}".format(fast, slow)
        signal = df.apply(
            lambda x: x[fast] < x[slow], axis=1).rename(system).to_frame()

    signal["prev"] = signal[system].shift(2)
    signal["curr"] = signal[system].shift(1)
    signal["entry"] = signal.apply(
        lambda x: x["prev"] is False and x["curr"] is True, axis=1)
    signal["exit"] = signal.apply(
        lambda x: x["prev"] is True and x["curr"] is False, axis=1)
    entry_exit = entry_exit_combine(signal, "entry", "exit")
    return entry_exit


if __name__ == "__main__":

    import sys
    indicators = sys.argv[0]
    df = pd.read_csv(indicators)
    entry_exit = buy_signal_cross(indicators, indicators.columns[0],
                                  indicators.columns[1])
    entry_exit.to_csv[1]
