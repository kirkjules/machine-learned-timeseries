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
    >>> from htp.api.oanda import Candles
    >>> ticker = "AUD_JPY"
    >>> arguments = {"from": "2018-02-05T22:00:00.000000000Z",
    ...              "granularity": "D", "smooth": True, "count": 200}
    >>> data = Candles.to_df(instrument=ticker, queryParameters=arguments)
    >>> avgs = []
    >>> for i in [3, 6, 12, 24]:
    ...     avg = smooth_moving_average(data, column="close", period=i)
    ...     avgs.append(avg)
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


def ichimoku_kinko_hyo(data, conv=9, base=26, lead=52):
    """
    A function to calculate the ichimoku kinko hyo indicator set.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    conv : int
        The window range used to calculate the tenkan sen signal.

    base : int
        The window range used to calculate the kijun sen signal.

    lead : int
        The window range used to calculate the senkou B signal.

    Returns
    -------
    pandas.core.frame.DataFrame
        A dataframe with identical timeseries index to parsed `data`, with
        columns respective to each signal that makes up the ichimoku kinko hyo
        indicator set.

    Notes
    -----
    Tenkan Sen: also know as the turning or conversion line. Calculated by
    averaging the highest high and the lowest low for the past 9 periods.
    Kijun Sen: also know as the standard or base line. Calculated by averaging
    the highest high and lowest low for the past 26 periods.
    Chikou Span: known as the lagging line. It is the given period's closing
    price 26 periods behind.
    Senkou Span: consists of two lines known as lead A and B. Lead A is
    calculated by averaging the Tenkan Sen and the Kijun Sen and plotting 26
    periods ahead. Lead B is calculated by averaging the highest high and
    lowest low for the past 52 periods and plotting 26 periods ahead.
    """

    CH = data["high"].rolling(conv).max().to_frame(name="CH")
    CL = data["low"].rolling(conv).min().to_frame(name="CL")

    tenkan = CH.merge(
        CL, left_index=True, right_index=True).mean(1).to_frame(name="tenkan")

    BH = data["high"].rolling(base).max().to_frame(name="BH")
    BL = data["low"].rolling(base).min().to_frame(name="BL")

    kijun = BH.merge(
        BL, left_index=True, right_index=True).mean(1).to_frame(name="kijun")

    chikou = data["close"].shift(-26).to_frame(name="chikou")

    senkou_A = tenkan.merge(
        kijun, left_index=True, right_index=True).mean(
            1).shift(26).to_frame(name="senkou_A")

    H = data["high"].rolling(lead).max().to_frame()
    L = data["low"].rolling(lead).min()
    senkou_B = H.merge(
        L, left_index=True, right_index=True).mean(
            1).shift(26).to_frame(name="senkou_B")

    return pd.concat([tenkan, kijun, chikou, senkou_A, senkou_B], axis=1)


def relative_strength_index(data, window=14):
    """
    Function to calculate the relative strength index (RSI) of a given ticker's
    timerseries data.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    prd : int
        The window range used to calculate the average gain and loss
        respectively.

    Returns
    -------
    pandas.core.frame.DataFrame
        A dataframe that contains the final RSI for a given period, as well as
        the calculated intermediary steps i.e. period-to-period price change,
        average gain and loss respectively and RS.
    """
    close_ = pd.to_numeric(data["close"])
    df = close_.diff().rename("Chg")
    sp = pd.concat([close_, df], axis=1)
    sp["Adv"] = sp["Chg"].mask(sp["Chg"] < 0, 0)
    sp["Decl"] = sp["Chg"].mask(sp["Chg"] > 0, 0).abs()
    sp["AvgGain"] = sp["Adv"].rolling(window).mean()
    sp["AvgLoss"] = sp["Decl"].rolling(window).mean()

    rd = {}
    cnt = 0
    gain = 0
    loss = 0
    for row in sp.iterrows():
        if cnt == 14:
            avg_gain = row[1]["AvgGain"]
            avg_loss = row[1]["AvgLoss"]
            rd[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                          "RS": (avg_gain / avg_loss)}
            gain = avg_gain
            loss = avg_loss
            cnt += 14
        elif cnt > 14:
            avg_gain = ((gain * 13) + row[1]["Adv"]) / 14
            avg_loss = ((loss * 13) + row[1]["Decl"]) / 14
            rd[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                          "RS": (avg_gain / avg_loss)}
            gain = avg_gain
            loss = avg_loss
            cnt += 1
        else:
            cnt += 1

    rd_df = pd.DataFrame.from_dict(rd, orient="index")
    rd_df["RSI"] = rd_df.apply(lambda x: 100 - (100 / (1 + x["RS"])), axis=1)

    return rd_df


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
