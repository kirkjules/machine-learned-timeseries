"""Module used to evaluate trade signals generated from analysis."""
import numpy as np


def entry_exit_combine(row, df, entry, exit):

    trade = False
    if row[entry] == True:
        print(row.name)
        reduct = df.loc[row.name:]
        exit = reduct[reduct[exit] == True].iterrows()
        try:
            trade = {"entry": row.name, "exit": next(exit)[0]}
        except StopIteration:
            trade = {"entry": row.name, "exit": np.nan}

    return trade


def buy_signal_cross(df, fast, slow):

    df = df.assign(comp=df[fast] > df[slow]).rename(
        {"comp": "{} > {}".format(fast, slow)}, axis="columns")

    df["Prev: {} > {}".format(fast, slow)] = df["{} > {}".format(fast, slow)
                                                ].shift(2)

    df["Curr: {} > {}".format(fast, slow)] = df["{} > {}".format(fast, slow)
                                                ].shift(1)

    entry = "{} {} buy entry".format(fast, slow)

    df[entry] = df.apply(
        lambda x: x["Prev: {} > {}".format(fast, slow)] is False and
        x["Curr: {} > {}".format(fast, slow)] is True, axis=1)

    exit = "{} {} buy exit".format(fast, slow)

    df[exit] = df.apply(
        lambda x: x["Prev: {} > {}".format(fast, slow)] is True and
        x["Curr: {} > {}".format(fast, slow)] is False, axis=1)

    ref = df.copy()

    df["Trade"] = df.apply(entry_exit_combine, axis=1, args=(ref, entry, exit))

    return df


def sell_signal_cross(df, fast, slow):

    pass
