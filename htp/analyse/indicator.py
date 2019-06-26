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

    Examples
    --------
    >>> import pandas as pd
    >>> from htp.api import oanda
    >>> from htp.analyse import indicator
    >>> ticker = "AUD_JPY"
    >>> arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                     "granularity": "D",
                     "smooth": True,
                     "count": 200}
    >>> data = oanda.Candles.to_df(instrument=ticker,
                                   queryParameters=arguments)
    >>> data_index_dt = data.set_index(
            pd.to_datetime(data.index,
                           format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
    >>> data_sorted = data_index_dt.sort_index()
    >>> avgs = []
    >>> for i in [3, 6, 12, 24, 48]:
            avg = indicator.smooth_moving_average(data_sorted, column="close",
                                                  period=i)
            avgs.append(avg)
    >>> pd.concat(avgs, axis=1).tail()
    """
    sma = df1[column].rolling(period).mean().rename(
        "{}_sma_{}".format(column, period))

    if concat:
        out = pd.concat([sma, df2], axis=1)
        return out

    return sma


if __name__ == "__main__":
    import sys
    data = pd.read_csv(sys.argv[1])
    sma_x = smooth_moving_average(data, column=sys.argv[2], period=sys.argv[3])
    sma_x_y = smooth_moving_average(data, df2=sma_x, column=sys.argv[2],
                                    concat=True, period=sys.argv[4])
    sma_x_y.to_csv("sma_{0}_{1}.csv".format(sys.argv[3], sys.argv[4]))
