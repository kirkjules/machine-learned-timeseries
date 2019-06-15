"""Module used to evaluate trade signals generated from analysis."""
import numpy as np


def entry_exit_combine(row, df, entry, exit):

    if row[entry] == True:
        reduct = df.loc[row.name:]
        exit = reduct[reduct[exit] == True].iterrows()
        try:
            trade_dt = [row.name, next(exit)[0]]
        except StopIteration:
            trade_dt = [row.name, np.nan]

    return trade_dt


def buy_signal_cross(df, fast, slow):

    system = "{} > {}".format(fast, slow)
    signal = df.apply(lambda x: x[fast] > x[slow], axis=1).rename(system)
    signal["prev"] = df[system].shift(2)
    signal["curr"] = df[system].shift(1)
    signal["entry"] = signal.apply(
        lambda x: x["prev"] is False and x["curr"] is True, axis=1)
    signal["exit"] = signal.apply(
        lambda x: x["prev"] is True and x["curr"] is False, axis=1)
    trade = signal.apply(entry_exit_combine, axis=1, result_type="expand",
                         args=(df, "entry", "exit"))

    return trade


def sell_signal_cross(df, fast, slow):

    pass
