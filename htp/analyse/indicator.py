"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

# import pandas as pd


def smooth_moving_average(df, column="close", period=10):

    df = df.assign(comp=lambda x: x[column].rolling(period).mean()
                   ).rename({"comp": "{}_sma_{}".format(column, period)},
                            axis=1)

    return df
