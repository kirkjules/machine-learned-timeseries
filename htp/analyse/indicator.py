"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

import pandas as pd


def smooth_moving_average(df1, df2=None, column="close", period=10,
                          concat=True):

    """
    df = df.assign(comp=lambda x: x[column].rolling(period).mean()
                   ).rename({"comp": "{}_sma_{}".format(column, period)},
                            axis=1)
    """
    sma = df1[column].rolling(period).mean().rename(
        "{}_sma_{}".format(column, period))

    if concat:
        out = pd.concat([sma, df2], axis=1)
        return out

    return sma
