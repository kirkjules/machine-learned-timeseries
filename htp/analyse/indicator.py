"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

import pandas as pd
from decimal import Decimal


def smooth_moving_average(df1, df2=None, column="close", period=10,
                          concat=False):
    """
    A function to calculate the rolling mean on a given dataframe column.

    Parameters
    ----------
    df1 : pandas.core.frame.DataFrame
        The dataframe from the given column will be specified to use when
        calculating the rolling mean.
    df2 : pandas.core.frame.DataFrame
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
    pandas.core.frame.DataFrame
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
    >>> avgs = []
    >>> for i in [3, 6, 12, 24]:
            avg = indicator.smooth_moving_average(data, column="close",
                                                  period=i)
            avgs.append(avg)
    >>> pd.set_option("display.max_columns", 6)
    >>> pd.concat(avgs, axis=1).tail()
                         close_sma_3  close_sma_6  close_sma_12  close_sma_24
    2018-11-05 22:00:00    81.749667    81.116833     80.314333     80.151417
    2018-11-06 22:00:00    82.134333    81.490667     80.538583     80.232458
    2018-11-07 22:00:00    82.518333    81.971667     80.796417     80.340250
    2018-11-08 22:00:00    82.530667    82.140167     81.043000     80.427208
    2018-11-11 22:00:00    82.227000    82.180667     81.218333     80.487708
    """
    rn = abs(Decimal(str(df1.iloc[0, 3])).as_tuple().exponent)
    sma = df1[column].rolling(period).mean().round(rn).rename(
        "{}_sma_{}".format(column, period))

    if concat:
        out = pd.concat([sma, df2], axis=1)
        return out

    return sma


if __name__ == "__main__":
    """
    python htp/analyse/indicator.py data/AUD_JPYH120180403-c100.csv close 3 6
    """

    import re
    import sys
    data = pd.read_csv(sys.argv[1], header=0,
                       names=["open", "high", "low", "close"],
                       index_col=0, parse_dates=True)
    sma_x = smooth_moving_average(data, column=sys.argv[2],
                                  period=int(sys.argv[3]))
    sma_x_y = smooth_moving_average(data, df2=sma_x, column=sys.argv[2],
                                    concat=True, period=int(sys.argv[4]))
    sf = "sma_{0}_{1}.csv".format(sys.argv[3], sys.argv[4])
    try:
        fn = "{0}_{1}".format(re.search(r"\/(.*?)\.csv", sys.argv[1]).group(1),
                              sf)
    except AttributeError:
        fn = sf
    sma_x_y.to_csv("data/{0}".format(fn))
