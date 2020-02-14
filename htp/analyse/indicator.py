"""
A collection of technical indicators that apply to timeseries in pandas
DataFrame format.
"""

import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_EVEN
# from htp.analyse.evaluate import iky_cat


def numpy_to_object_array(array, exp):
    """Convert float elements in a numpy 1d array to string objects via decimal
    e.g. ti_sma = numpy_to_object_array(ti_sma, '0.001')"""
    arr = []
    for element in array:
        dec = Decimal(element).quantize(Decimal(exp), rounding=ROUND_HALF_EVEN)
        arr.append(str(dec))

    return np.asarray(arr, dtype='object')


class Indicate:
    def __init__(self, data=None, labels=[], orient='rows', exp=3):
        """Base class to validate data and pre-process before computing
        indicator values.

        Parameters
        ----------
        data : None, list, numpy.ndarray, pandas.core.series.Series,
        pandas.core.frame.DataFrame
            Ticker timeseries data provided in a format that is interpolated
            into a numpy ndarray with shape length of index by number of
            columns. Maximum five columns will be recognised if sufficient
            labels are provided.

        labels : list
            A list of strings that define what each column's data represent.
            Common definitions are timestamp, open, high, low, and close.

        orient : str {'rows', 'columns'}
            Optional argument to orient numpy array for processing. Logic has
            not been written to handle incorrect orientation.

        exp : int
            The number of decimal places values should be rounded to.

        Attributes
        ----------
        data : dict
            A dictionary of arrays indexed by label items or column names.

        Examples
        --------
        >>> df = pd.DataFrame({
        ...  'timestamp': array([Timestamp('2020-01-29 17:30:00'),
        ...                      Timestamp('2020-01-29 17:45:00')],
        ...                     dtype=object),
        ...  'open': array(['73.632', '73.641'], dtype=object),
        ...  'high': array(['73.642', '73.670'], dtype=object),
        ...  'low': array(['73.628', '73.640'], dtype=object),
        ...  'close': array(['73.641', '73.654'], dtype=object)})
        >>> Indicate(df).data
        {'timestamp': array([Timestamp('2020-01-29 17:30:00'),
 Timestamp('2020-01-29 17:45:00')],    dtype=object), 'open': array(['73.632',
 '73.641'], dtype=object), 'high': array(['73.642', '73.670'], dtype=object),
 'low': array(['73.628', '73.640'], dtype=object), 'close': array(['73.641',
 '73.654'], dtype=object)}
        """
        self.data = {}

        if data is None:
            raise ValueError('No data was parsed')

        elif isinstance(data, list):
            item_length = None
            # compare items in list
            for item in data:
                if not isinstance(item, list):
                    raise TypeError('Each item in the list must a be a list \
itself, defined by a string at the same index in labels.')
                elif item_length is not None and item_length != len(item):
                    raise ValueError('Each item in the list must be equal in \
length.')
                else:
                    item_length = len(item)
            if len(data) != len(labels):
                raise ValueError('Unequal number of labels to columns \
provided.')
            elif len(data) == 1:
                self.data[labels[0]] = np.asarray(data[0], dtype=float)
            else:
                for ind in range(len(data)):
                    self.data[labels[ind]] = np.asarray(data[ind], dtype=float)

        elif isinstance(data, np.ndarray):  # map out each ndarray shape to be
            # accepted.
            if orient == 'rows':
                if data.shape[1] != len(labels):
                    raise ValueError('Unequal number of labels to columns \
provided.')
                else:
                    columns = np.split(data,  data.shape[1], axis=1)
                    for ind in range(len(columns)):
                        self.data[labels[ind]] = np.concatenate(columns[ind])\
                            .astype(float)
            elif orient == 'columns':
                if data.shape[0] != len(labels):
                    raise ValueError('Unequal number of labels to columns \
provided.')
                else:
                    for ind in range(len(data)):
                        self.data[labels[ind]] = data[ind].astype(float)

        elif isinstance(data, pd.core.series.Series):
            if not labels and data.name is None:
                raise ValueError('No label available to describe data, add \
name to Series or to labels list variable')
            elif len(labels) > 1 and data.name is None:
                raise ValueError('Too many items in labels, only provide one \
item with Series data.')
            elif len(labels) == 1:
                self.data[labels[0]] = data.astype(float).to_numpy()
            elif not labels:
                self.data[data.name] = data.astype(float).to_numpy()

        elif isinstance(data, pd.core.frame.DataFrame):
            columns = np.split(data.to_numpy(), len(data.columns), axis=1)
            for ind in range(len(columns)):
                try:
                    self.data[data.columns[ind]] =\
                            np.concatenate(columns[ind]).astype(float)
                except TypeError:
                    self.data[data.columns[ind]] = np.concatenate(columns[ind])

        self.exp = f".{'1'.zfill(exp)}"

    def smooth_moving_average(self, period, label='close'):
        """
        A function to calculate the rolling mean on a given dataframe column.

        Parameters
        ----------
        period : int
            The number of periods that contribute to the mean.
        label : str
            The dictionary key in data that point to which array the rolling
            mean is calculated.

        Returns
        -------
        dict
            A dictionary with the key structured against a set nomenclature,
            lable_period_sma, and the value a numpy array with dtype object.

        Examples
        --------
        >>> df = pd.DataFame(
        ...  {'close': array(
        ...     ['73.663', '73.632', '73.611', '73.640', '73.607', '73.632',
        ...      '73.608', '73.594', '73.586', '73.562', '73.614', '73.636',
        ...      '73.630', '73.604', '73.558', '73.511', '73.536', '73.458',
        ...      '73.388', '73.408'], dtype=object)})
        >>> Indicate(df).smooth_moving_average(2)
        {'close_sma_2': array(['NaN', '73.648', '73.621', '73.625', '73.623',
                '73.619', '73.620', '73.601', '73.590', '73.574', '73.588',
                '73.625', '73.633', '73.617', '73.581', '73.535', '73.524',
                '73.497', '73.423', '73.398'], dtype=object)}
        """
        sma = pd.Series(self.data[label]).rolling(period).mean().to_numpy()

        d = {f'{label}_sma_{period}': numpy_to_object_array(sma, self.exp)}

        return d

    def ichimoku_kinko_hyo(self, conv=9, base=26, lead=52):
        """
        A function to calculate the ichimoku kinko hyo indicator set.

        Parameters
        ----------
        conv : int
            The window range used to calculate the tenkan sen signal.
        base : int
            The window range used to calculate the kijun sen signal.
        lead : int
            The window range used to calculate the senkou B signal.

        Returns
        -------
        dict
           A dictionary with an entry for each value array that defines the
           ichimoku kinko hyo indicator.

        Notes
        -----
        - Tenkan Sen: also know as the turning or conversion line. Calculated
        by averaging the highest high and the lowest low for the past 9
        periods.
        - Kijun Sen: also know as the standard or base line. Calculated by
        averaging the highest high and lowest low for the past 26 periods.
        - Chikou Span: known as the lagging line. It is the given period's
        closing price 26 periods behind.
        - Senkou Span: consists of two lines known as lead A and B. Lead A is
        calculated by averaging the Tenkan Sen and the Kijun Sen and plotting
        26 periods ahead. Lead B is calculated by averaging the highest high
        and lowest low for the past 52 periods and plotting 26 periods ahead.

        Examples
        --------
        """
        CH = pd.Series(self.data["high"]).rolling(conv).max().to_numpy()
        CL = pd.Series(self.data["low"]).rolling(conv).min().to_numpy()
        tenkan = np.mean(np.stack([CH, CL], axis=1), axis=1)

        BH = pd.Series(self.data["high"]).rolling(base).max().to_numpy()
        BL = pd.Series(self.data["low"]).rolling(base).min().to_numpy()
        kijun = np.mean(np.stack([BH, BL], axis=1), axis=1)

        chikou = np.append(
            self.data["close"][26:], [np.nan for i in range(26)])

        senkou_A = np.append(
            [np.nan for i in range(26)],
            np.mean(np.stack([tenkan, kijun], axis=1), axis=1))

        H = pd.Series(self.data["high"]).rolling(lead).max().to_numpy()
        L = pd.Series(self.data["low"]).rolling(lead).min().to_numpy()
        senkou_B = np.append(
            [np.nan for i in range(26)],
            np.mean(np.stack([H, L], axis=1), axis=1))

        return {'tenkan': numpy_to_object_array(tenkan, self.exp),
                'kijun': numpy_to_object_array(kijun, self.exp),
                'chikou': numpy_to_object_array(chikou, self.exp),
                'senkou_A': numpy_to_object_array(senkou_A, self.exp),
                'senkou_B': numpy_to_object_array(senkou_B, self.exp)}

    def relative_strength_index(self, period=14):
        """
        Function to calculate the relative strength index (RSI) of a given
        ticker's timerseries data.

        Parameters
        ----------
        period : int
            The window range used to calculate the average gain and loss
            respectively.

        Returns
        -------
        dict
            A dictionary with key-value pairs for the final RSI for a given
            period, as well as the calculated intermediary steps i.e. period-to
            -period price change, average gain and loss respectively and RS.

        Notes
        -----
        - Momentum indicator that measures the magnitude or velocity of recent
        price changes.
        - I.e. RSI was designed to measure the speed of price movement.
        - Evaluates overbought (>70) and oversold (<30) conditions.
        - Rises as the number and size of positive closes increases, conversely
        lowers as the number and size of losses increases.
        - Indicator can remain "overbought" or "oversold" while the ticker
        continues in an up- or downtrend respectively.

        References
        ----------
        - https://www.investopedia.com/terms/r/rsi.asp
        - https://www.babypips.com/learn/forex/relative-strength-index

        Examples
        --------
        """
        chg = np.append([0.], np.diff(self.data['close']))
        adv = np.where(chg > 0, chg, 0)
        decl = np.absolute(np.where(chg < 0, chg, 0))
        rows = np.stack([adv, decl], axis=1)
        rsi = np.zeros((len(rows), 1))

        gains = []
        losses = []
        with np.nditer([rows, rsi], flags=['reduce_ok', 'multi_index'],
                       op_flags=[['readonly'], ['readwrite']]) as it:
            for item, RSI in it:
                if it.multi_index[0] <= 13:
                    if it.multi_index[1] == 0:
                        gains.append(item)
                        avg_gain = np.mean(gains)
                        gain = avg_gain
                    else:
                        losses.append(item)
                        avg_loss = np.mean(losses)
                        loss = avg_loss
                else:
                    if it.multi_index[1] == 0:
                        avg_gain = ((gain * 13) + item) / 14
                        gain = avg_gain
                    else:
                        avg_loss = ((loss * 13) + item) / 14
                        loss = avg_loss
                if it.multi_index[1] == 1:
                    if avg_loss == 0.:
                        RS = 0.
                    else:
                        RS = avg_gain / avg_loss
                    RSI[...] = 100. - (100. / (1. + RS))

        return {'rsi': numpy_to_object_array(np.concatenate(rsi), self.exp)}

    def stochastic(self, period=14, smoothK=1, smoothD=3):
        """
        Function to calculate the stochastic oscillator of a given ticker's
        timerseries data.

        Parameters
        ----------
        period : int
            The window range used to calculate the %K value.
        smoothK : int
            The number of periods used to smooth the %K signal line.
        smoothD : int
            The number of periods used to smooth the %K signal line resulting
            in a lagging %D signal line.

        Returns
        -------
        dict
            A dataframe that contains the %K and %D values that make up the
            stochastic oscillator.

        Notes
        -----
        - Stochastic results spot checked against Oanda values yielding slight
        variances.
        - Momentum indicator that compares a given closing price to a range of
        prices over a given time frame.
        - Theory assumes that closing prices should close near the same
        direction as the current trend.
        - Overbought/Oversold: primary signal generated.
        - Default thresholds are overbought @ >80 and oversold @ <20.
        - Best to trade with the trend when identifyng Stochastic overbought
        & oversold levels, as overbought does not always mean a bearish move
        ahead and vice versa.
        - I.e. wait for the trend to reverse and confirm with overbought/
        oversold stochastic signal.
        - Divergence: occurs when movements in price are not confirmed by the
        stochastic oscillator.
        - Bullish when price records a lower low, but stochastic records a
        higher high. Vice versa for bearish divergence.
        - Bull/Bear setups are the inverse of divergence.
        - Bull setup when price records a lower high, but Stochastic records
        a higher high. The setup then results in a dip in price which is a
        bullish entry point before price rises. Opposite for bear setup.
        - Note that overbought/oversold signal are the most objective signal
        type, where divergence and bull/bear setups are subjective in their
        interpretation of the chart's visual pattern. Refer to TradingView
        documentation (www.tradingview.com/wiki/Stochastic_(STOCH)) for
        examples.

        Examples
        --------
        """
        minN = pd.Series(self.data["low"]).rolling(period).min().to_numpy()
        maxN = pd.Series(self.data["high"]).rolling(period).max().to_numpy()
        nominator = self.data["close"] - minN
        denominator = maxN - minN
        k = np.divide(nominator, denominator, out=np.zeros_like(nominator),
                      where=denominator != 0)
        percK = k * 100.
        percK = pd.Series(percK).rolling(smoothK).mean().to_numpy()
        percD = pd.Series(percK).rolling(smoothD).mean().to_numpy()
        return {'percK': numpy_to_object_array(percK, self.exp),
                'percD': numpy_to_object_array(percD, self.exp)}

    def moving_average_convergence_divergence(self, fast=12, slow=26,
                                              signal=9):
        """
        Function to calculate the moving average convergence divergence for a
        given ticker's timerseries data.

        Parameters
        ----------
        fast : int
            The window range used to calculate the fast period exponential
            moving average.
        slow : int
            The window range used to calculate the slow period exponential
            moving average.
        signal : int
            The window range used to calculate the fast-slow difference moving
            average.

        Returns
        -------
        dict
            A dataframe that contains the MACD, signal and histogram values
            that make up the stochastic oscillator.

        Notes
        -----
        - MACD results spot checked as accurate against Oanda values.
        - Used to identify momentum in a given timeseries' trend, as well as
        direction and duration.
        - Two different indicator types, combined into one.
        - Employs two moving qverages with different lengths (lagging
        indicators), to identify trend direction and duration.
        - Difference between moving averages makes up the MACD line.
        - MACD exponential moving average gives the Signal line.
        - The difference between these two lines gives a histogram that
        oscillates above and below a centre Zero Line.
        - The histogram indicates on the timeseries' momentum.
        - Basic interpretation: when MACD is positive and the histogram is
        increasing, then upside momentum is increasing, and vice versa.
        - Signal line crossovers: most common signal.
        - Bullish when the MACD crosses above the Signal, vice versa.
        - Signficant because the Signal is effectively an indicator of the
        MACD and any subsequent movement may signify a potentially strong move.
        - Zero line crossovers: similar presence to signal line crossover.
        - Bullish when MACD crosses above the Zero line therefore going from
        negative to positive. Opposite for bearish signal.
        - Divergence: when the MACD and actual price do not agree.
        - Bullish when price records a lower low, but MACD presents a higher
        high. Vice versa for bearish divergence.
        - The signal suggests a change in momentum and can sometimes precede a
        significant reversal.
        - Do not use to identify overbought or oversold conditions because this
        indicator is not bound to a range.

        Examples
        --------
        """
        emaF = pd.Series(self.data["close"]).ewm(span=fast, min_periods=fast)\
            .mean().to_numpy()
        emaS = pd.Series(self.data["close"]).ewm(
            span=slow, min_periods=slow).mean().rename("emaS")
        macd = emaF - emaS
        signal = pd.Series(macd).ewm(span=signal, min_periods=signal).mean()\
            .to_numpy()
        histogram = macd - signal

        return {'macd': numpy_to_object_array(macd, self.exp),
                'signal': numpy_to_object_array(signal, self.exp),
                'histogram': numpy_to_object_array(histogram, self.exp)}

    def momentum(self):
        """
        Defines Average True Range and Average Directional Movement
        indicators respectively.

        Parameters
        ----------
        period : int
            The window range used for number both the ATR, ADX and Wilder
            smoothing calculations.

        Notes
        -----
        - ATR results spot checked as accurate against Oanda values.
        - ADX results spot checked against Oanda values yielding slight
        variances.
        - ATR and ADX both volatility indicators that answer different
        questions.
        - ADX objectively answers whether, for a given period, the timeseries
        is in a high or low volatility environment.
        - The ADX is comparable across tickers, date ranges or time periods.
        - ATR defines what is a statistically significant price move for a
        particular ticker on a specific time frame.
        - ATR does not inform on price direction.
        - ATR basic interpretation is the higher the value, the higher the
        volatility.
        - ATR used to measure a move's strength.
        - When a ticker moves or reverses in a bullish or bearish direction
        this is usually accompanied by increased volatility. --> The more
        volatility in a large move, the more interest or pressure there is
        reinforcing that move.
        - When a ticker is trading sideways the volatility is relatively low.
        - ADX indicates trend strength.
        - Wilder believed that ADX > 25 indicated a strong trend, while < 20
        indicated a weak or non-trend.
        - Note, this is not set in stone for a given ticker and should be
        interpreted by taking into consideration historical values.
        - For ML study, choose to keep this value as continuous, rather than
        binary.
        - ADX also yields crossover signals that require a condition set to be
        met:
        - Bullish DI Cross requires (A) ADX > 25, (B) +DI > -DI, (C) Stop
        Loss set @ current session close, (D) Signal strengthens if ADX
        increases.
        - Bearish DI Cross is the inverse to the bullish setup.

        Examples
        --------
        """
        HL = self.data['high'] - self.data['low']
        HpC = np.absolute(self.data['high'] - np.roll(self.data['close'], 1))
        LpC = np.absolute(self.data['low'] - np.roll(self.data['close'], 1))

        TR = np.amax(np.stack((HL, HpC, LpC), axis=-1), axis=1)
        TR[0] = HL[0]
        return TR

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

    def average_true_range(self):
        return {'atr':
                numpy_to_object_array(self._w_avg_a(self.momentum()), self.exp)
                }

    def average_directional_movement(self):
        """
        Function to calculate the average directional movement index for a
        given ticker's timeseries data.
        """
        HpH = self.data['high'] - np.roll(self.data['high'], 1)
        pLL = np.roll(self.data['low'], 1) - self.data['low']
        DMp = np.where(np.greater(HpH, pLL) & np.greater(HpH, 0), HpH, 0)
        DMm = np.where(np.greater(pLL, HpH) & np.greater(pLL, 0), pLL, 0)
        DM = np.stack((DMp, DMm, self.momentum()), axis=-1)
        DI = self._w_avg_b(DM)
        DIp = DI[:, 0] / DI[:, 2] * 100
        DIm = DI[:, 1] / DI[:, 2] * 100
        DX = np.absolute(DIp - DIm) / np.absolute(DIp + DIm) * 100
        adx = self._w_avg_a(DX, ind=28)
        return {'adx': numpy_to_object_array(adx, self.exp)}


if __name__ == "__main__":
    """
    python htp/analyse/indicator.py data/AUD_JPYH120180403-c100.csv close 3 6
    """

    import re
    import sys
    data = pd.read_csv(sys.argv[1], header=0,
                       names=["open", "high", "low", "close"],
                       index_col=0, parse_dates=True)
    # sma_x = smooth_moving_average(data, column=sys.argv[2],
    #                               period=int(sys.argv[3]))
    # sma_x_y = smooth_moving_average(data, df2=sma_x, column=sys.argv[2],
    #                                 concat=True, period=int(sys.argv[4]))
    sf = "sma_{0}_{1}.csv".format(sys.argv[3], sys.argv[4])
    try:
        fn = "{0}_{1}".format(re.search(r"\/(.*?)\.csv", sys.argv[1]).group(1),
                              sf)
    except AttributeError:
        fn = sf
    # sma_x_y.to_csv("data/{0}".format(fn))
