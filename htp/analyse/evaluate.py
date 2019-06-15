"""Module used to evaluate trade signals generated from analysis."""
import numpy as np


def entry_exit_combine(row, df, entry, exit):

    if row[entry] == True:
        reduct = df[row.name:]
        exit = reduct[reduct[exit] == True].iterrows()
        try:
            return [row.name, next(exit)[0]]
        except StopIteration:
            return [row.name, np.nan]
    else:
        return [np.nan, np.nan]


def buy_signal_cross(df, fast, slow):

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
    return entry_exit


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
    sma_5 = indicator.smooth_moving_average(data, column="close", period=5)
    sma_5_10 = indicator.smooth_moving_average(data, df2=sma_5, column="close",
                                               concat=True, period=10)
    entry_exit = buy_signal_cross(sma_5_10, "close_sma_5", "close_sma_10")
    print(entry_exit)
