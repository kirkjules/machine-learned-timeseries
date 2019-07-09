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
    2018-11-05 22:00:00       81.750       81.117        80.314        80.151
    2018-11-06 22:00:00       82.134       81.491        80.539        80.232
    2018-11-07 22:00:00       82.518       81.972        80.796        80.340
    2018-11-08 22:00:00       82.531       82.140        81.043        80.427
    2018-11-11 22:00:00       82.227       82.181        81.218        80.488
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
    - Tenkan Sen: also know as the turning or conversion line. Calculated by \
    averaging the highest high and the lowest low for the past 9 periods.
    - Kijun Sen: also know as the standard or base line. Calculated by \
    averaging the highest high and lowest low for the past 26 periods.
    - Chikou Span: known as the lagging line. It is the given period's \
    closing price 26 periods behind.
    - Senkou Span: consists of two lines known as lead A and B. Lead A is \
    calculated by averaging the Tenkan Sen and the Kijun Sen and plotting 26 \
    periods ahead. Lead B is calculated by averaging the highest high and \
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


def relative_strength_index(data, period=14):
    """
    Function to calculate the relative strength index (RSI) of a given ticker's
    timerseries data.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    period : int
        The window range used to calculate the average gain and loss
        respectively.

    Returns
    -------
    pandas.core.frame.DataFrame
        A dataframe that contains the final RSI for a given period, as well as
        the calculated intermediary steps i.e. period-to-period price change,
        average gain and loss respectively and RS.

    Notes
    -----
    - Momentum indicator that measures the magnitude or velocity of recent \
    price changes.
    - I.e. RSI was designed to measure the speed of price movement.
    - Evaluates overbought (>70) and oversold (<30) conditions.
    - Rises as the number and size of positive closes increases, conversely \
    lowers as the number and size of losses increases.
    - Indicator can remain "overbought" or "oversold" will ticker present in \
    an up- or downtrend respectively.

    References
    ----------
    - https://www.investopedia.com/terms/r/rsi.asp
    - https://www.babypips.com/learn/forex/relative-strength-index

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> data = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> relative_strength_index(data).tail()
                         avg_gain  avg_loss        RS        RSI
    2018-10-04 19:00:00  0.017276  0.046083  0.374887  27.266741
    2018-10-04 20:00:00  0.022042  0.042791  0.515103  33.997907
    2018-10-04 21:00:00  0.020467  0.043734  0.467992  31.879716
    2018-10-04 22:00:00  0.021434  0.040611  0.527793  34.546108
    2018-10-04 23:00:00  0.021617  0.037710  0.573253  36.437432
    """
    close_ = pd.to_numeric(data["close"])
    df = close_.diff().rename("Chg")

    s = pd.concat([close_, df], axis=1)
    s["Adv"] = s["Chg"].mask(s["Chg"] < 0, 0)
    s["Decl"] = s["Chg"].mask(s["Chg"] > 0, 0).abs()
    s["AvgGain"] = s["Adv"].rolling(period).mean()
    s["AvgLoss"] = s["Decl"].rolling(period).mean()

    r = {}
    count = 0
    gain = 0
    loss = 0
    avg_gain = 0
    avg_loss = 0
    for row in s.iterrows():
        if count == 14:
            avg_gain = row[1]["AvgGain"]
            avg_loss = row[1]["AvgLoss"]
            r[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                         "RS": (avg_gain / avg_loss)}
        elif count > 14:
            avg_gain = ((gain * 13) + row[1]["Adv"]) / 14
            avg_loss = ((loss * 13) + row[1]["Decl"]) / 14
            r[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                         "RS": (avg_gain / avg_loss)}
        gain = avg_gain
        loss = avg_loss
        count += 1

    rs = pd.DataFrame.from_dict(r, orient="index")
    rs["RSI"] = rs.apply(lambda x: 100 - (100 / (1 + x["RS"])), axis=1)

    return rs


def stochastic(data, period=14):
    """
    Function to calculate the stochastic oscillator of a given ticker's
    timerseries data.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    period : int
        The window range used to %K value.

    Returns
    -------
    pandas.core.frame.DataFrame
        A dataframe that contains the %K and %D values that make up the
        stochastic oscillator.

    Notes
    -----
    - Momentum indicator that compares a given closing price to a range of \
    prices over stated time period.
    - Generates overbought (>80) and oversold (<20) signals by using a 0-100 \
    value range.
    - Theory predicates on the assumption that closing prices should close \
    near the same direction as the current trend.
    - Stochastic therefore works best in consistent trading ranges.

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> data = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> stochastic(data).tail()
                          close    minN    maxN       %K       %D
    2018-10-04 19:00:00  80.562  80.381  81.088  25.6011  21.0681
    2018-10-04 20:00:00  80.646  80.381  81.056  39.2593  29.6824
    2018-10-04 21:00:00  80.590  80.381  81.028  32.3029  32.3878
    2018-10-04 22:00:00  80.624  80.381  81.028  37.5580  36.3734
    2018-10-04 23:00:00  80.648  80.381  81.028  41.2674  37.0428
    """
    minN = data["low"].rolling(period).min().rename("minN")
    maxN = data["high"].rolling(period).max().rename("maxN")
    s = pd.concat([pd.to_numeric(data["close"]), minN, maxN], axis=1)
    s["%K"] = s.apply(
        lambda x: 100 * (x["close"] - x["minN"]) / (x["maxN"] - x["minN"]),
        axis=1)
    s["%D"] = s["%K"].rolling(3).mean()

    return s.round(4)


def moving_average_convergence_divergence(data, fast=12, slow=26, signal=9):
    """
    Function to calculate the moving average convergence divergence for a given
    ticker's timerseries data.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    fast : int
        The window range used to calculate the fast period exponential moving
        average.

    slow : int
        The window range used to calculate the slow period exponential moving
        average.

    signal : int
        The window range used to calculate the fast-slow difference moving
        average.


    Returns
    -------
    pandas.core.frame.DataFrame
        A dataframe that contains the fast and slow exponential moving
        averages, MACD, signal and histogram values that make up the moving
        average convergence divergence indicator.

    Notes
    -----
    - Used to identify moving averages that are indicating a new trend, \
    whether bullish or bearish.

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> data = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> moving_average_convergence_divergence(data).tail()
                            emaF     emaS    MACD  signal    hist
    2018-10-04 19:00:00  80.6989  80.9230 -0.2241 -0.1965 -0.0276
    2018-10-04 20:00:00  80.6907  80.9024 -0.2117 -0.2020 -0.0097
    2018-10-04 21:00:00  80.6752  80.8793 -0.2041 -0.2071  0.0030
    2018-10-04 22:00:00  80.6674  80.8604 -0.1930 -0.2105  0.0175
    2018-10-04 23:00:00  80.6644  80.8447 -0.1803 -0.2101  0.0298
    """

    emaF = data["close"].ewm(
        span=fast, min_periods=fast).mean().rename("emaF")
    emaS = data["close"].ewm(
        span=slow, min_periods=slow).mean().rename("emaS")
    e = pd.concat([emaF, emaS], axis=1)
    e["MACD"] = e["emaF"] - e["emaS"]
    e["signal"] = e["MACD"].rolling(signal).mean()
    e["hist"] = e["MACD"] - e["signal"]

    return e.round(4)


class Momentum:

    def __init__(self, data, period=14):

        self.high = pd.to_numeric(data["high"], errors="coerce")
        self.low = pd.to_numeric(data["low"], errors="coerce")
        self.close = pd.to_numeric(data["close"], errors="coerce")

        HL = (self.high - self.low).rename("HL")
        HpC = (self.high - self.close.shift(1)).abs().rename("HpC")
        LpC = (self.low - self.close.shift(1)).abs().rename("LpC")

        tr = pd.concat([HL, HpC, LpC], axis=1)
        tr["TR"] = tr.max(axis=1)

        d = self._wilder_average_a(tr, "TR", period)
        ATR = pd.DataFrame.from_dict(
            d, orient="index").rename(columns={0: "ATR"})

        atr = tr.merge(
            ATR, how="left", left_index=True, right_index=True, validate="1:1")
        self.atr = atr
        self.period = period

    def _wilder_average_a(self, df, column, length):

        d = {}
        X = 0
        prevX = 0
        count = 0
        df[f"r{length}{column}"] = df[column].rolling(length).mean()
        for row in df.iterrows():
            if count == length:
                X = row[1][f"r{length}{column}"]
                d[row[0]] = X
            elif count > length:
                X = (prevX * (length - 1) + row[1][column]) / length
                d[row[0]] = X
            prevX = X
            count += 1

        return d

    def _wilder_average_b(self, df, column, length):

        d = {}
        X = 0
        prevX = 0
        count = 0
        df[f"r{length}{column}"] = df[column].rolling(length).sum()
        for row in df.iterrows():
            if count == length:
                X = row[1][f"r{length}{column}"]
                d[row[0]] = X
            elif count > length:
                X = prevX - (prevX / length) + row[1][column]
                d[row[0]] = X
            prevX = X
            count += 1

        return d

    @classmethod
    def average_true_range(cls, *args, **kwargs):
        return cls(*args, **kwargs).atr

    def _ADX_DM_logic(self, row, colA, colB):

        if row[colA] > row[colB] and row[colA] > 0:
            return row[colA]
        else:
            return 0

    @classmethod
    def average_directional_movement(cls, *args, **kwargs):
        """
        Function to calculate the average directional movement index for a
        given ticker's timeseries data.
        """
        n = cls(*args, **kwargs)
        HpH = (n.high - n.high.shift(1)).rename("HpH")
        pLL = (n.low.shift(1) - n.low).rename("pLL")

        DM = pd.concat([HpH, pLL], axis=1)
        DM["+DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("HpH", "pLL"))
        DM["-DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("pLL", "HpH"))

        uDMdic = n._wilder_average_b(DM, "+DM", n.period)
        uDM = pd.DataFrame.from_dict(
            uDMdic, orient="index").rename(columns={0: "+DM14"})

        dDMdic = n._wilder_average_b(DM, "-DM", n.period)
        dDM = pd.DataFrame.from_dict(
            dDMdic, orient="index").rename(columns={0: "-DM14"})

        TRdic = n._wilder_average_b(n.atr, "TR", n.period)
        TR14 = pd.DataFrame.from_dict(
            TRdic, orient="index").rename(columns={0: "TR14"})

        DI = pd.concat([uDM, dDM, TR14], axis=1)
        DI["+DI"] = DI["+DM14"] / DI["TR14"] * 100
        DI["-DI"] = DI["-DM14"] / DI["TR14"] * 100
        DI["DX"] = (DI["+DI"] - DI["-DI"]).abs() /\
            (DI["+DI"] + DI["-DI"]).abs() *\
            100

        adx_comp = DI.iloc[:].copy(deep=True)
        adx_dict = n._wilder_average_a(adx_comp, "DX", n.period)
        adx_frame = pd.DataFrame.from_dict(
            adx_dict, orient="index").rename(columns={0: "ADX"})
        ADX = DI.merge(
            adx_frame, how="left", left_index=True, right_index=True,
            validate="1:1")

        return ADX.round(4)


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
