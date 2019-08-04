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
        The number of periods that contribute to the mean.
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
    >>> arguments = {"from": "2018-02-05T22:00:00.000000000Z",
    ...              "granularity": "H1", "smooth": True, "count": 200}
    >>> data = Candles.to_df(instrument="AUD_JPY", queryParameters=arguments)
    >>> avgs = []
    >>> for i in [3, 6, 12, 24]:
    ...     avg = smooth_moving_average(data, column="close", period=i)
    ...     avgs.append(avg)
    >>> pd.set_option("display.max_columns", 6)
    >>> pd.concat(avgs, axis=1).tail()
                         close_sma_3  close_sma_6  close_sma_12  close_sma_24
    2018-02-16 01:00:00       84.301       84.295        84.271        84.415
    2018-02-16 02:00:00       84.335       84.318        84.271        84.413
    2018-02-16 03:00:00       84.367       84.338        84.315        84.408
    2018-02-16 04:00:00       84.341       84.321        84.322        84.394
    2018-02-16 05:00:00       84.324       84.330        84.313        84.384
    """
    rn = abs(Decimal(str(df1.iloc[0, 3])).as_tuple().exponent)
    sma = df1[column].rolling(period).mean().round(rn).to_frame(
        name="{}_sma_{}".format(column, period))

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


def stochastic(data, period=14, smoothK=1, smoothD=3):
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
    - Stochastic results spot checked against Oanda values yielding slight \
    variances.
    - Momentum indicator that compares a given closing price to a range of \
    prices over stated time period.
    - Theory predicates on the assumption that closing prices should close \
    near the same direction as the current trend.
    - Overbought/Oversold: primary signal generated.
        - Default thresholds are overbought @ >80 and oversold @ <20.
        - Best to trade with the trend when identifyng Stochastic overbought \
        & oversold levels, as overbought does not always mean a bearish move \
        ahead and vice versa.
        - I.e. wait for the trend to reverse and confirm with overbought/ \
        oversold Stochastic signal.
    - Divergence: occurs when movements in price are not confirmed by the \
    Stochastic oscillator.
        - Bullish when price records a lower low, but Stochastic records a \
        higher high. Vice versa for bearish divergence.
    - Bull/Bear setups are the inverse of divergence.
        - Bull setup when price records a lower high, but Stochastic records \
        a higher high. The setup then results in a dip in price which is a \
        bullish entry point before price rises. Opposite for bear setup.
    - Note that overbought/oversold signal are the most objective signal \
    type, where divergence and bull/bear setups a subjective in their \
    interpretation of the chart's visual pattern. Refer to TradingView \
    documentation (www.tradingview.com/wiki/Stochastic_(STOCH)) for examples.

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
        axis=1).rolling(smoothK).mean()
    s["%D"] = s["%K"].rolling(smoothD).mean()

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
    - MACD results spot checked as accurate against Oanda values.
    - Used to identify momentum in a given timeseries' trend, as well as \
    direction and duration.
    - Two different indicator types, combined into one.
    - Employs to Moving Averages with different lengths (lagging indicators), \
    to identify trend direction and duration.
    - Difference between moving averages makes up MACD line.
    - MACD exponential moving average gives the Signal line.
    - The difference between these two lines gives a histogram that oscillates \
    above and below a centre Zero Line.
    - The histogram indicates on the timeseries' momentum.
    - Basic interpretation: when MACD is positive and the histogram is \
    increasing, then upside momentum is increasing, and vice versa.
    - Signal line crossovers: most common signal.
        - Bullish when the MACD crosses above the Signal, vice versa.
        - Signficant because the Signal is effectively an indicator of the \
        MACD and any subsequent movement may signify a potentially strong move.
    - Zero line crossovers: similar presence to signal line crossover.
        - Bullish when MACD crosses above the Zero line therefore going from \
        negative to positive. Opposite for bearish signal.
    - Divergence: when the MACD and actual price do not agree.
        - Bullish when price records a lower low, but MACD presents a higher \
        high. Vice versa for bearish divergence.
        - The signal suggests a change in momentum and can sometimes precede a\
        significant reversal.
    - Do not use to identify overbought or oversold conditions because this \
    indicator is not bound to a range.

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> data = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> moving_average_convergence_divergence(data).tail()
                            emaF     emaS    MACD  Signal  Histogram
    2018-10-04 19:00:00  80.6989  80.9230 -0.2241 -0.2030    -0.0211
    2018-10-04 20:00:00  80.6907  80.9024 -0.2117 -0.2047    -0.0070
    2018-10-04 21:00:00  80.6752  80.8793 -0.2041 -0.2046     0.0005
    2018-10-04 22:00:00  80.6674  80.8604 -0.1930 -0.2023     0.0093
    2018-10-04 23:00:00  80.6644  80.8447 -0.1803 -0.1979     0.0176
    """

    emaF = data["close"].ewm(
        span=fast, min_periods=fast).mean().rename("emaF")
    emaS = data["close"].ewm(
        span=slow, min_periods=slow).mean().rename("emaS")
    e = pd.concat([emaF, emaS], axis=1)
    e["MACD"] = e["emaF"] - e["emaS"]
    e["Signal"] = e["MACD"].ewm(
        span=signal, min_periods=signal).mean()
    e["Histogram"] = e["MACD"] - e["Signal"]

    return e.round(4)


class Momentum:
    """
    Class that defines Average True Range and Average Directional Movement
    indicators respectively.

    The class instantiates with the ATR pre-generated. The ADX can then be
    called as a class method. As both indicators were conceived and defined
    by Wilder, smoothing calculation also follow Wilder's directions. Here,
    the class outlines both of Wilder's smoothing techniques as they are
    applied in the ATR and ADX calculation.

    Parameters
    ----------
    data : pandas.core.frame.DataFrame
        The dataframe that contains the timeseries open, high, low, close data
        for a given ticker.

    period : int
        The window range used for number both the ATR, ADX and Wilder smoothing
        calculations.

    Attributes
    -------
    high : pandas.Series
        Returns the `high` column from the parsed dataset with values converted
        to np.float38.

    low : pandas.Series
        Returns the `low` column from the parsed dataset with values converted
        to np.float38.

    close : pandas.Series
        Returns the `close` column from the parsed dataset with values
        converted to np.float38.

    atr : pandas.core.frame.DataFrame
        Returns a dataframe with `HL`, `HpC`, `LpC`, `TR` and `ATR` columns.

    period : int
        Returns the parsed period parameter.

    Notes
    -----
    - ATR results spot checked as accurate against Oanda values.
    - ADX results spot checked against Oanda values yielding slight variances.
    - ATR and ADX both volatility indicators that answer different questions.
    - ADX objectively answers whether, for a given period, the timeseries is \
    in a high or low volatility environment.
        - The ADX is comparable across tickers, date ranges or time periods.
    - ATR defines what is a statistically significant price move for a \
    particular ticker on a specific time frame.
    - ATR does not inform on price direction.
    - ATR basic interpretation is the higher the value, the higher the \
    volatility.
    - ATR used to measure a move's strength.
        - Where a ticker moves or reverses in a bullish or bearish direction \
        this is usually accompanied by increased volatility. --> The more \
        volatility in a large move, the more interest or pressure there is \
        reinforcing that move.
        - Where a ticker is trading sideways the volatility is relatively low.
    - ADX indicates trend strength.
        - Wilder believed that ADX > 25 indicated a strong trend, while < 20 \
        indicated a weak or non-trend.
        - Note, this is not set in stone for a given ticker and should be \
        interpreted by taking into consideration historical values.
        - For ML study, choose to keep this value as continuous, rather than \
        binary.
    - ADX also yields crossover signals that require a condition set to be met:
        - Bullish DI Cross requires (A) ADX > 25, (B) +DI > -DI, (C) Stop \
        Loss set @ current session close, (D) Signal strengthens if ADX \
        increases.
        - Bearish DI Cross is the inverse to the bullish setup.

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> data = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> Momentum.average_true_range(data).tail()
                            HL    HpC    LpC     TR     r14TR       ATR
    2018-10-04 19:00:00  0.092  0.030  0.062  0.092  0.166643  0.152344
    2018-10-04 20:00:00  0.114  0.096  0.018  0.114  0.162786  0.149605
    2018-10-04 21:00:00  0.051  0.018  0.069  0.069  0.152286  0.143848
    2018-10-04 22:00:00  0.064  0.061  0.003  0.064  0.142000  0.138144
    2018-10-04 23:00:00  0.117  0.061  0.056  0.117  0.138357  0.136634
    >>> Momentum.average_directional_movement(data).tail()
                          +DM14   -DM14    TR14      +DI      -DI       DX      ADX
    2018-10-04 19:00:00  0.1609  0.6406  2.1328   7.5458  30.0354  59.8425  55.9301
    2018-10-04 20:00:00  0.2254  0.5948  2.0945  10.7637  28.4006  45.0330  55.1518
    2018-10-04 21:00:00  0.2093  0.5524  2.0139  10.3949  27.4275  45.0330  54.4290
    2018-10-04 22:00:00  0.2174  0.5129  1.9340  11.2402  26.5199  40.4652  53.4316
    2018-10-04 23:00:00  0.2359  0.4763  1.9129  12.3301  24.8978  33.7588  52.0264
    """

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

        DM = pd.concat([HpH, pLL, n.atr["TR"]], axis=1)
        DM["+DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("HpH", "pLL"))
        DM["-DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("pLL", "HpH"))

        # StockCharts (school.stockcharts.com/doku.php?id=technical_indicators:
        # average_directional_index_adx)
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

        adx_copy = DI.iloc[:].copy(deep=True)
        adx_dict = n._wilder_average_a(adx_copy, "DX", n.period)
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
