"""Module used to evaluate trade signals generated from analysis."""
import numpy as np
import pandas as pd


def entry_exit_combine(row, df, entry, exit):
    """
    A function to assign entry and exit timestamps for a given signal.

    The function is designed to be called as an argument to a pandas dataframe
    apply function.

    Parameters
    ----------
    df : pandas.DataFrame
        The target dataframe that contains `entry` and `exit` labelled columns.
    entry : str
        The `entry` column label. This column will contain either True or False
        values, indicating whether a trade should be entered (True) or not
        (False).
    exit : str
        The `exit` column label. This column will contain either True or False
        values, indicating whether a trade should be exited (True) or not
        (False).

    Returns
    -------
    list
        The list will contain two values. The first value is the timestamp for
        when a trade should be entered. The second value is the timestamp for
        when the corresponding trade should be exited.
    """
    if row[entry] == True:
        reduct = df[row.name:]
        exit = reduct[reduct[exit] == True].iterrows()
        try:
            return [row.name, next(exit)[0]]
        except StopIteration:
            return [row.name, np.nan]
    else:
        return [np.nan, np.nan]


def entry_exit_combine_(df, entry, exit):

    en = df.entry[df[entry] == True].reset_index()
    en = en.drop("entry", axis=1).rename(columns={"index": "entry"})
    print(en.loc[0][0])
    ex = df.exit[df[exit] == True].reset_index()
    ex = ex.drop("exit", axis=1).rename(columns={"index": "exit"})
    print(ex.loc[0][0])

    if ex.loc[0][0] < en.loc[0][0]:
        ex_clean = ex.drop([0], inplace=False)
        del ex
        ex = ex_clean.reset_index(drop=True, inplace=False)

    out = pd.concat([en, ex], axis=1)
    return out


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
    trade = signal.apply(entry_exit_combine, axis=1, result_type="expand",
                         args=(signal, "entry", "exit")).rename(
                             columns={0: "entry", 1: "exit"})
    entry_exit = trade[~trade["entry"].isnull()].reset_index(drop=True)
    trade_ = entry_exit_combine_(signal, "entry", "exit")
    return entry_exit, trade_


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
    entry_exit, trade_ = buy_signal_cross(
        sma_5_10, "close_sma_5", "close_sma_10")
    print(entry_exit)
    print(trade_)
