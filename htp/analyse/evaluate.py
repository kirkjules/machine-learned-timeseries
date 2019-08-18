"""Module used to evaluate trade signals generated from analysis."""
import pandas as pd


def entry_exit_combine(df, entry, exit):
    """
    A function to combine entry and exit timestamps for trades generated via
    signal cross logic.

    Parameters
    ----------
    df : pandas.core.frame.DataFrame
        The dataframe that contains the trade signals with respective entry and
        exit columns.

    entry : str
        The label for the column containing entry timestamps.

    exit : str
        The label for the column containing exit timestamps.

    Returns
    -------
    pandas.core.frame.DataFrame
        Dataframe will contain two columns, designated "entry" and "exit"
        respectively. Each row is one trade.
    """
    en_prep = df.entry[df[entry] == True].reset_index()
    en = en_prep.drop("entry", axis=1).rename(columns={"index": "entry"})
    ex_prep = df.exit[df[exit] == True].reset_index()
    ex = ex_prep.drop("exit", axis=1).rename(columns={"index": "exit"})

    # Checking that first signal is not an "exit" which would result in a mis-
    # alignment between entry and exit singals that will not correspond to the
    # same trade.
    # Note: see test script that qualifies the implied logic used to combine
    # entry and exit signal.
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
    df : pandas.core.frame.DataFrame
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
    pandas.core.frame.DataFrame
        A pandas dataframe that will contain two columns containing the entry
        and exit timestamps respectively for a trade.

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> from htp.analyse import indicator, evaluate
    >>> data_sorted = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> sma_5 = indicator.smooth_moving_average(
    ...     data_sorted, column="close", period=5)
    >>> sma_5_10 = indicator.smooth_moving_average(
    ...     data_sorted, column="close", df2=sma_5, concat=True, period=10)
    >>> signal_cross(sma_5_10, "close_sma_5", "close_sma_10").head(5)
                    entry                exit
    0 2018-06-12 02:00:00 2018-06-12 10:00:00
    1 2018-06-13 03:00:00 2018-06-13 20:00:00
    2 2018-06-14 15:00:00 2018-06-14 17:00:00
    3 2018-06-15 06:00:00 2018-06-15 11:00:00
    4 2018-06-18 08:00:00 2018-06-18 14:00:00    
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


def iky_cat(row):
    """
    To categorise the order in which ichimoku signal lines present with respect
    to each other.
    """
    ls = list(row.sort_values().index)
    cat = "_".join(ls)
    return cat


if __name__ == "__main__":
    """
    python htp/analyse/evaluate.py data/sma_3_6.csv
    """

    import sys
    import re
    data = pd.read_csv(sys.argv[1], header=0, names=["entry", "exit"],
                       index_col=0, parse_dates=True)
    entry_exit = signal_cross(data, data.columns[0], data.columns[1])
    sf = "entry_exit.csv".format()
    try:
        fn = "{0}_{1}".format(re.search(r"\/(.*?)\.csv", sys.argv[1]).group(1),
                              sf)
    except AttributeError:
        fn = sf
    entry_exit.to_csv("data/{0}".format(fn))
