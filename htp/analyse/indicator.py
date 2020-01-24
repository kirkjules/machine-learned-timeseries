"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

import numpy as np
import pandas as pd
from decimal import Decimal


def smooth_moving_average(df1, df2=None, column="close", period=10,
                          concat=False):
    """
    A function to calculate the rolling mean on a given dataframe column.

    Parameters
    ----------
    df1 : pandas.core.frame.DataFrame
        A dataframe containing a column label matching the `column` keyword
        variable.
    df2 : pandas.core.frame.DataFrame
        An optional second dataframe on which to concatenate the generated
        rolling mean dataframe. Used when an existing indicator dataframe has
        been created. Both dataframe should posess the same index.
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
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data = store["data_mid"]
    >>> avgs = []
    >>> for i in [3, 6, 12, 24]:
    ...     avg = smooth_moving_average(data, column="close", period=i)
    ...     avgs.append(avg)
    >>> pd.set_option("display.max_columns", 6)
    >>> pd.concat(avgs, axis=1).tail()
                         close_sma_3  close_sma_6  close_sma_12  close_sma_24
    timestamp
    2019-08-20 19:45:00       72.009       72.023        72.034        72.062
    2019-08-20 20:00:00       71.999       72.017        72.030        72.057
    2019-08-20 20:15:00       72.001       72.015        72.026        72.052
    2019-08-20 20:30:00       71.998       72.004        72.019        72.047
    2019-08-20 20:45:00       71.997       71.998        72.016        72.043
    """
    # rn = abs(Decimal(str(df1.iloc[0, 3])).as_tuple().exponent)
    sma = df1[column].rolling(period).mean().round(6).to_frame(
        name="{}_sma_{}".format(column, period))

    if concat:
        out = pd.concat([sma, df2], axis=1)
        return out

    return sma.round(6)


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
        A dataframe with identical timeseries index to input `data`, with
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

    Examples
    --------
    >>> import pandas as pd
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data = store["data_mid"]
    >>> ichimoku_kinko_hyo(data).tail()
                          tenkan    kijun  chikou  senkou_A  senkou_B
    timestamp
    2019-08-20 19:45:00  72.0240  72.0680     NaN   72.0515   72.1505
    2019-08-20 20:00:00  72.0225  72.1005     NaN   72.0340   72.1345
    2019-08-20 20:15:00  72.0225  72.0915     NaN   72.0680   72.1345
    2019-08-20 20:30:00  72.0210  72.0720     NaN   72.0680   72.1345
    2019-08-20 20:45:00  72.0125  72.0530     NaN   72.0680   72.1345
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

    return pd.concat([tenkan, kijun, chikou, senkou_A, senkou_B],
                     axis=1).round(6)


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
    - Indicator can remain "overbought" or "oversold" while ticker continues \
    in an up- or downtrend respectively.

    References
    ----------
    - https://www.investopedia.com/terms/r/rsi.asp
    - https://www.babypips.com/learn/forex/relative-strength-index

    Examples
    --------
    >>> import pandas as pd
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data = store["data_mid"]
    >>> relative_strength_index(data).tail()
                         avg_gain  avg_loss      RS      RSI
    2019-08-20 19:45:00    0.0048    0.0101  0.4737  32.1443
    2019-08-20 20:00:00    0.0059    0.0094  0.6255  38.4788
    2019-08-20 20:15:00    0.0066    0.0087  0.7562  43.0585
    2019-08-20 20:30:00    0.0061    0.0113  0.5451  35.2806
    2019-08-20 20:45:00    0.0075    0.0105  0.7159  41.7220
    """
    close_ = pd.to_numeric(data["close"])
    # diff() method calculates the difference of a DataFrame element compared
    # with another element in the DataFrame, default is the element in the
    # same column in the previous row.
    df = close_.diff().rename("Chg")

    s = pd.concat([close_, df], axis=1)
    # mask() method replaces values where the condition is True.
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
    for row in s.itertuples():  # iterrows():
        if count == 14:
            avg_gain = row[5]  # ["AvgGain"]
            avg_loss = row[6]  # ["AvgLoss"]
            r[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                         "RS": (avg_gain / avg_loss)}
        elif count > 14:
            avg_gain = ((gain * 13) + row[3]) / 14  # Adv
            avg_loss = ((loss * 13) + row[4]) / 14  # Decl
            r[row[0]] = {"avg_gain": avg_gain, "avg_loss": avg_loss,
                         "RS": (avg_gain / avg_loss)}
        gain = avg_gain
        loss = avg_loss
        count += 1

    rs = pd.DataFrame.from_dict(r, orient="index")
    rs["RSI"] = rs.apply(lambda x: 100 - (100 / (1 + x["RS"])), axis=1)

    return rs.round(6)


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
        The window range used to calculate the %K value.
    smoothK : int
        The number of periods used to smooth the %K signal line.
    smoothD : int
        The number of periods used to smooth the %K signal line resulting in \
        a lagging %D signal line.

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
    prices over a given time frame.
    - Theory assumes that closing prices should close near the same direction \
    as the current trend.
    - Overbought/Oversold: primary signal generated.
        - Default thresholds are overbought @ >80 and oversold @ <20.
        - Best to trade with the trend when identifyng Stochastic overbought \
        & oversold levels, as overbought does not always mean a bearish move \
        ahead and vice versa.
        - I.e. wait for the trend to reverse and confirm with overbought/ \
        oversold stochastic signal.
    - Divergence: occurs when movements in price are not confirmed by the \
    stochastic oscillator.
        - Bullish when price records a lower low, but stochastic records a \
        higher high. Vice versa for bearish divergence.
    - Bull/Bear setups are the inverse of divergence.
        - Bull setup when price records a lower high, but Stochastic records \
        a higher high. The setup then results in a dip in price which is a \
        bullish entry point before price rises. Opposite for bear setup.
    - Note that overbought/oversold signal are the most objective signal \
    type, where divergence and bull/bear setups are subjective in their \
    interpretation of the chart's visual pattern. Refer to TradingView \
    documentation (www.tradingview.com/wiki/Stochastic_(STOCH)) for examples.

    Examples
    --------
    >>> import pandas as pd
    >>> with pd.HDFStore("data/EUR_USD/M15/price.h5") as store:
    ...     data = store["M"]
    >>> stochastic(data).tail()
                              %K       %D
    2019-11-29 20:45:00   6.8583  15.0773
    2019-11-29 21:00:00  19.4767  15.1739
    2019-11-29 21:15:00  29.8653  18.7334
    2019-11-29 21:30:00  74.0207  41.1209
    2019-11-29 21:45:00  47.2185  50.3682
    """
    minN = data["low"].rolling(period).min().to_numpy()
    maxN = data["high"].rolling(period).max().to_numpy()
    nominator = data.close.values - minN
    denominator = maxN - minN
    k = np.divide(nominator, denominator, out=np.zeros_like(nominator),
                  where=denominator != 0)
    percK = k * 100
    s = pd.DataFrame(data=percK, index=data.index, columns=['K'])
    s["%K"] = s["K"].rolling(smoothK).mean()
    s.drop('K', axis=1, inplace=True)
    s["%D"] = s["%K"].rolling(smoothD).mean()
    return s.round(6)


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
    - Employs two moving qverages with different lengths (lagging indicators),\
    to identify trend direction and duration.
    - Difference between moving averages makes up the MACD line.
    - MACD exponential moving average gives the Signal line.
    - The difference between these two lines gives a histogram that oscillates\
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
    >>> import pandas as pd
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data = store["data_mid"]
    >>> moving_average_convergence_divergence(data).tail()
                            emaF     emaS    MACD  Signal  Histogram
    timestamp
    2019-08-20 19:45:00  72.0311  72.0502 -0.0191 -0.0145    -0.0047
    2019-08-20 20:00:00  72.0266  72.0466 -0.0200 -0.0156    -0.0044
    2019-08-20 20:15:00  72.0253  72.0445 -0.0192 -0.0163    -0.0029
    2019-08-20 20:30:00  72.0174  72.0393 -0.0219 -0.0174    -0.0045
    2019-08-20 20:45:00  72.0146  72.0363 -0.0217 -0.0183    -0.0035
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

    return e.round(6)


class Momentum:
    """
    Class that defines Average True Range and Average Directional Movement
    indicators respectively.

    The class instantiates with the ATR pre-generated. The ADX can then be
    called as a class method. As both indicators were conceived and defined
    by Wilder, smoothing calculations also follow Wilder's directions. These
    calculations are defined within the class as internal functions.

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
        - When a ticker moves or reverses in a bullish or bearish direction \
        this is usually accompanied by increased volatility. --> The more \
        volatility in a large move, the more interest or pressure there is \
        reinforcing that move.
        - When a ticker is trading sideways the volatility is relatively low.
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
    >>> import pandas as pd
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data = store["data_mid"]
    >>> Momentum.average_true_range(data).tail()
                            HL    HpC    LpC     TR   r14TR     ATR
    timestamp
    2019-08-20 19:45:00  0.043  0.010  0.033  0.043  0.0345  0.0438
    2019-08-20 20:00:00  0.031  0.026  0.005  0.031  0.0329  0.0429
    2019-08-20 20:15:00  0.024  0.016  0.008  0.024  0.0322  0.0415
    2019-08-20 20:30:00  0.044  0.000  0.044  0.044  0.0339  0.0417
    2019-08-20 20:45:00  0.051  0.034  0.017  0.051  0.0356  0.0424
    >>> Momentum.average_directional_movement(data).tail()
                             +DI      -DI       DX      ADX
    2019-08-20 19:45:00  14.2501  24.6096  26.6587  17.3978
    2019-08-20 20:00:00  13.5141  23.8383  27.6401  18.1294
    2019-08-20 20:15:00  14.6763  22.8542  21.7899  18.3909
    2019-08-20 20:30:00  13.5702  24.5575  28.8170  19.1356
    2019-08-20 20:45:00  12.4034  25.3121  34.2267  20.2136
    """

    def __init__(self, data, period=14):

        self.index = data.index
        self.high = data.high.to_numpy()
        self.low = data.low.to_numpy()
        self.close = data.close.to_numpy()

        HL = self.high - self.low
        HpC = np.absolute(self.high - np.roll(self.close, 1))
        LpC = np.absolute(self.low - np.roll(self.close, 1))

        TR = np.amax(np.stack((HL, HpC, LpC), axis=-1), axis=1)
        TR[0] = HL[0]
        self.TR = TR

    def _w_avg_a(self, a, ind=14):
        with np.nditer([a, None]) as it:
            X = 0
            count = 0
            prevX = 0
            for x, y in it:
                if count < ind - 1:
                    y[...] = np.nan
                elif count == ind - 1:
                    X = np.mean(a[ind - 14:ind])
                    y[...] = X
                elif count > ind - 1:
                    X = (prevX * 13 + x) / 14
                    y[...] = X
                prevX = X
                count += 1
            return it.operands[1]

    @classmethod
    def average_true_range(cls, *args, **kwargs):
        base = cls(*args, **kwargs)
        atr = base._w_avg_a(base.TR)
        return pd.DataFrame(
            data=atr, index=base.index, columns=['ATR']).round(6)

    @classmethod
    def average_directional_movement(cls, *args, **kwargs):
        """
        Function to calculate the average directional movement index for a
        given ticker's timeseries data.
        """

        base = cls(*args, **kwargs)
        HpH = base.high - np.roll(base.high, 1)
        pLL = np.roll(base.low, 1) - base.low
        DMp = np.where(np.greater(HpH, pLL) & np.greater(HpH, 0), HpH, 0)
        DMm = np.where(np.greater(pLL, HpH) & np.greater(pLL, 0), pLL, 0)
        DM = np.stack((DMp, DMm, base.TR), axis=-1)
        DI = base._w_avg_b(DM)
        DIp = DI[:, 0] / DI[:, 2] * 100
        DIm = DI[:, 1] / DI[:, 2] * 100
        DX = np.absolute(DIp - DIm) / np.absolute(DIp + DIm) * 100
        adx = base._w_avg_a(DX, ind=28)
        return pd.DataFrame(
            data=adx, index=base.index, columns=['ADX']).round(6)

    def _w_avg_b(self, a):
        with np.nditer([a, None]) as it:
            X = 0
            col = 1
            count = 1
            prevX = np.zeros(3)
            for x, y in it:
                if count < 15:
                    y[...] = np.nan
                elif count == 15:
                    X = np.sum(a[1:15, col - 1])
                    y[...] = X
                elif count > 15:
                    X = prevX[col - 1] - (prevX[col - 1] / 14) + x
                    y[...] = X
                prevX[col - 1] = X
                if col < 3:
                    col += 1
                elif col == 3:
                    col = 1
                    count += 1
            return it.operands[1]


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
