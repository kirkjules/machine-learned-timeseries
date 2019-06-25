"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

import pandas as pd


def smooth_moving_average(df1, df2=None, column="close", period=10,
                          concat=False):
    """
    A function to calculate the rolling mean on a given dataframe column.

    Parameters
    ----------
    df1 : pandas.DataFrame
        The dataframe from the given column will be specified to use when
        calculating the rolling mean.
    df2 : pandas.DataFrame
        An optional second dataframe on which to concatenate the generated
        rolling mean. Used when an existing indicator dataframe has been
        started.
    column : str
        The column name in df1 on which to calculate the rolling mean.
    period : int
        The number of periods that contribute the mean.
    concat : bool
        If the generated rolling mean result should be concatenated to the
        specified (`df2`) dataframe.

    Returns
    -------
    pandas.DataFrame
        A dataframe with either the index of df1 and a single column containing
        the calculated rolling mean.
        Or, the above, concatenated to the specified dataframe `df2`.
    """
    sma = df1[column].rolling(period).mean().rename(
        "{}_sma_{}".format(column, period))

    if concat:
        out = pd.concat([sma, df2], axis=1)
        return out

    return sma


if __name__ == "__main__":

    from htp.api import oanda
    ticker = "AUD_JPY"
    arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                 "granularity": "D",
                 "smooth": True,
                 "count": 200}
    data = oanda.Candles.to_df(instrument=ticker, queryParameters=arguments)
    sma_5 = smooth_moving_average(data, column="close", period=5)
    sma_5_10 = smooth_moving_average(data, df2=sma_5, column="close",
                                     concat=True, period=10)
    print(sma_5_10.head(20))
    avgs = []
    for i in [3, 6, 12, 24, 48]:
        avg = smooth_moving_average(data, column="close", period=i)
        avgs.append(avg)
