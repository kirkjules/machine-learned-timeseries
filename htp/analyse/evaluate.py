"""Module used to evaluate trade signals generated from analysis."""
import numpy as np


def entry_exit_combine(row, df, entry, exit):

    trade = False
    if row[entry] == True:
        reduct = df.loc[row.name:]
        exit = reduct[reduct[exit] == True].iterrows()
        try:
            trade = {"entry": row.name, "exit": next(exit)[0]}
        except StopIteration:
            trade = {"entry": row.name, "exit": np.nan}

    return trade


def buy_signal_cross(df, fast, slow):

    system = "{} > {}".format(fast, slow)
    prev = "Prev: {}".format(system)
    curr = "Curr: {}".format(system)

    signal = df[df[fast] > df[slow]]
    df[prev] = df[system].shift(2)
    df[curr] = df[system].shift(1)

    entry = "{} buy entry".format(system)

    df[entry] = df.apply(lambda x: x[prev] is False and x[curr] is True,
                         axis=1)

    exit = "{} buy exit".format(system)

    df[exit] = df.apply(lambda x: x[prev] is True and x[curr] is False, axis=1)

    ref = df.copy()

    df["Trade"] = df.apply(entry_exit_combine, axis=1, args=(ref, entry, exit))

    return df


def sell_signal_cross(df, fast, slow):

    pass
