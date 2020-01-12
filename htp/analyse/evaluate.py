"""Module used to evaluate trade signals generated from analysis."""

import sys
import copy
import numpy as np
import pandas as pd
from tqdm import tqdm
from loguru import logger
from decimal import Decimal, ROUND_HALF_EVEN


class Signals:
    """
    Function to calculate and apply a stop loss to each trade.

    By default the system generates an exit signal. This is the base TP/SL.
    A set stop loss is a value set x pips from the entry price. The exit signal
    is generated by the low (buy) or high (sell) crossing that threshold before
    the default system exit is generated.
    A trailing stop loss is a value that is re-calculated each session based on
    a given logic. If the low or high crosses the current threshold for that
    session an exit signal is generated.

    Parameters
    ----------
    df_mid : pandas.core.frame.DataFrame
        The dataframe containing a ticker's mid price for a session's open,
        high, low & close.
    df_entry : pandas.core.frame.DataFrame
        The dataframe containing either the ticker's ask or bid price for a
        session's open, high, low & close. This is the price at which the trade
        enters. For a buy trade, the entry price is the ask, for a sell trade,
        the entry price is the bid.
    df_exit : pandas.core.frame.DataFrame
        The dataframe containing either the ticker's ask or bid price for a
        session's open, high, low & close. This is the price at which the trade
        exits. For a buy trade, the exit is the bid, for a sell trade, the exit
        is the ask.
    df_sys : pandas.core.frame.DataFrame
        A dataframe possessing two columns, indexed by timestamp. Both columns
        contain values that define a standalone signal line. These signals will
        be assessed to cross, thereby establishing entry and exit actions.
    fast : str
        The column label for the faster moving signal line in the df_sys
        dataframe.
    slow : str
        The column label for the slower moving signal line in the df_sys
        dataframe.
    trade : {"buy", "sell"}
        The trade direction the system will be assessed against.
    stop_delta : float
        The number of pips the default stop loss will be established away from
        the trade entry price. Always a positive number, internal logic adjusts
        for buy and sell trades.

    Attributes
    ----------
    sys_en : pandas.core.frame.DataFrame
        A dataframe containing two columns: the entry timestamp and respective
        price value for a buy or sell trade, generated by an appropriately
        defined signal cross in the system.
    sys_ex : pandas.core.frame.DataFrame
        A dataframe containing two columns: the exit timestamp and respective
        price value for a buy or sell trade, generated by an appropriately
        defined signal cross in the system.
    stop_delta : float
        The stop_pips_delta parameters returned either positive or negative
        depending on trade direction. Positive difference sets the stop higher
        than the open for a sell trade, vice versa for a buy trade.
    raw_signals : pandas.core.frame.DataFrame
        A raw dataset with mid candle price values, entry and exit signals
        generated by a given system, a stop loss column derived from the
        stop_delta and the ohlc exit (ask or bid) candle prices.

    Examples
    --------
    >>> import pandas as pd
    >>> from htp.analyse import indicator
    >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
    ...     data_mid = store["data_mid"]
    ...     data_ask = store["data_ask"]
    ...     data_bid = store["data_bid"]
    >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
    >>> sma_6_24 = indicator.smooth_moving_average(
    ...     data_mid, df2=sma_6, period=24, concat=True)
    >>> Signals(data_mid, data_ask, data_bid, sma_6_24, "close_sma_6",
    ...     "close_sma_24").raw_signals.iloc[282875:282890, 4:9]
                        entry_type  entry_price exit_type  exit_price set_stop_loss
    exit_dt
    2019-08-20 14:15:00        NaN          NaN       NaN         NaN          exit
    2019-08-20 14:30:00        NaN          NaN       NaN         NaN          exit
    2019-08-20 14:45:00       True       72.097       NaN         NaN        71.990
    2019-08-20 15:00:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 15:15:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 15:30:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 15:45:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 16:00:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 16:15:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 16:30:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 16:45:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 17:00:00        NaN          NaN       NaN         NaN        71.990
    2019-08-20 17:15:00        NaN          NaN      True      72.053          exit
    2019-08-20 17:30:00        NaN          NaN       NaN         NaN          exit
    2019-08-20 17:45:00        NaN          NaN       NaN         NaN          exit
    """
    def __init__(self, df_mid, df_entry, df_exit, df_sys, fast, slow,
                 trade="buy", stop_delta=0.5, rounder=3):

        self.trade = trade
        self.df_mid = df_mid
        self.df_entry = df_entry
        self.df_exit = df_exit
        self.rounder = rounder

        self.stop_delta = abs(stop_delta)
        if trade == "buy":
            self.stop_delta = -abs(stop_delta)

        self.sys_en = self._signal(
            df_sys, fast, slow, trade=trade, df_price=df_entry)
        self.sys_ex = self._signal(
            df_sys, fast, slow, trade=trade, df_price=df_exit, signal="exit")
        # "close" // exit, like entry, would occur at a session's start.

        sys_entry = df_mid.merge(
            self.sys_en, how="left", left_index=True, right_on="entry_dt",
            validate="1:1")
        sys_entry.set_index("entry_dt", inplace=True)
        sys_entry_exit = sys_entry.merge(
            self.sys_ex, how="left", left_index=True, right_on="exit_dt",
            validate="1:1")
        sys_entry_exit.set_index("exit_dt", inplace=True)

        sys_entry_exit["stop_loss_by_limit"] = sys_entry_exit.apply(
            self._stop_loss_by_limit, pips=self.stop_delta, axis=1,
            exp=self.rounder)
        sys_entry_exit["stop_loss_by_limit"].fillna(
            method="ffill", inplace=True)

        df_exit.rename(
            columns={"high": "exit_high", "low": "exit_low"}, inplace=True)
        self.raw_signals = sys_entry_exit.merge(
            df_exit, how="left", left_index=True, right_index=True,
            validate="1:1")

    @classmethod
    def sys_signals(cls, *args, **kwargs):
        """
        Fuction to return trades with entry and exit signals derived from a
        given SMA cross system.

        Examples
        --------
        >>> import pandas as pd
        >>> from htp.analyse import indicator
        >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        ...     data_mid = store["data_mid"]
        ...     data_ask = store["data_ask"]
        ...     data_bid = store["data_bid"]
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.sys_signals(data_mid, data_ask, data_bid, sma_6_24,
        ...                     "close_sma_6", "close_sma_24").tail()
                  entry_datetime  entry_price       exit_datetime  exit_price
        7627 2019-08-19 04:45:00       72.139 2019-08-19 09:00:00      72.138
        7628 2019-08-19 09:30:00       72.197 2019-08-19 14:30:00      72.159
        7629 2019-08-19 19:45:00       72.159 2019-08-19 20:00:00      72.110
        7630 2019-08-20 02:15:00       72.264 2019-08-20 07:30:00      72.150
        7631 2019-08-20 14:45:00       72.097 2019-08-20 17:15:00      72.053
        """
        k = cls(*args, **kwargs)
        d = []
        en = False
        signal_data = {}
        logger.info(
            f"Generating signals from {k.raw_signals.iloc[0].name} to "
            f"{k.raw_signals.iloc[-1].name}\n")

        for row in tqdm(k.raw_signals.itertuples()):
            if row[5] is True and en is False:
                signal_data["entry_datetime"] = row[0]
                signal_data["entry_price"] = row[6]
                en = True
            elif row[7] is True and en is True:
                signal_data["exit_datetime"] = row[0]
                signal_data["exit_price"] = row[8]
                d.append(copy.deepcopy(signal_data))
                en = False

        return pd.DataFrame(d)

    @classmethod
    def limit_stop_signals(cls, *args, **kwargs):
        """
        Fuction to return trades with entry signals derived from a given
        SMA cross system, and exit signals set by either the system or, if
        crossed, a stop loss limit at a given price difference from entry.

        Examples
        --------
        >>> import pandas as pd
        >>> from htp.analyse import indicator
        >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        ...     data_mid = store["data_mid"]
        ...     data_ask = store["data_ask"]
        ...     data_bid = store["data_bid"]
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.limit_stop_signals(
        ...     data_mid, data_ask, data_bid, sma_6_24, "close_sma_6",
        ...     "close_sma_24", trade="buy", stop_delta=0.2).head()
               entry_datetime  entry_price       exit_datetime exit_price
        0 2008-06-02 11:00:00      100.216 2008-06-02 11:15:00    100.096
        1 2008-06-02 20:30:00       99.860 2008-06-02 20:45:00     99.740
        2 2008-06-03 02:00:00      100.044 2008-06-03 04:00:00     99.924
        3 2008-06-03 09:00:00       99.786 2008-06-03 17:30:00    100.139
        4 2008-06-04 02:00:00      100.430 2008-06-04 07:45:00    100.422
        """
        k = cls(*args, **kwargs)
        k.raw_signals["ex_type_by_limit"] = k.raw_signals.apply(
            k._signal_stop_loss, args=("stop_loss_by_limit", k.trade), axis=1)

        return k._generate_trades(
            k.raw_signals[
                ["entry_type", "entry_price", "exit_type", "exit_price",
                 "stop_loss_by_limit", "ex_type_by_limit"]])

    @classmethod
    def atr_stop_signals(cls, df_prop, *args, atr_multiplier=3, **kwargs):
        """
        Fuction to return trades with entry signals derived from a given
        SMA cross system, and exit signals set by either the system or, if
        crossed, a stop loss limit x * ATR from the entry price.

        Examples
        --------
        >>> import pandas as pd
        >>> from htp.analyse import indicator
        >>> with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        ...     data_mid = store["data_mid"]
        ...     data_ask = store["data_ask"]
        ...     data_bid = store["data_bid"]
        >>> data_prop = indicator.Momentum(data_mid)
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.atr_stop_signals(
        ...     data_prop.atr, data_mid, data_ask, data_bid, sma_6_24,
        ...     "close_sma_6", "close_sma_24").head()
               entry_datetime  entry_price       exit_datetime exit_price
        0 2008-06-02 11:00:00      100.216 2008-06-02 13:45:00    100.006
        1 2008-06-02 20:30:00       99.860 2008-06-03 00:00:00      99.56
        2 2008-06-03 02:00:00      100.044 2008-06-03 04:15:00     99.860
        3 2008-06-03 09:00:00       99.786 2008-06-03 17:30:00    100.139
        4 2008-06-04 02:00:00      100.430 2008-06-04 07:45:00    100.422
        """
        k = cls(*args, **kwargs)
        # ATR values shifted for calculations, i.e. use previous sessions's ATR
        # to define current session's SL.
        atr_shift = df_prop["ATR"].shift(1)
        stop_loss = k.raw_signals.merge(
            atr_shift, how="left", left_index=True, right_index=True,
            validate="1:1")

        stop_loss["prev_close_1"] = stop_loss["close_x"].shift(1)
        stop_loss["prev_close_2"] = stop_loss["close_x"].shift(2)
        stop_loss["stop_loss_by_ATR"] = stop_loss.apply(
            k._stop_loss_by_atr, args=(atr_multiplier, k.trade,), axis=1,
            exp=k.rounder)
        stop_loss["stop_loss_by_ATR"].fillna(method="ffill", inplace=True)
        stop_loss["ex_type_by_ATR"] = stop_loss.apply(
            k._signal_stop_loss, args=("stop_loss_by_ATR", k.trade), axis=1)

        return k._generate_trades(
            stop_loss[
                ["entry_type", "entry_price", "exit_type", "exit_price",
                 "stop_loss_by_ATR", "ex_type_by_ATR"]])

    def _signal(self, df_sys, fast, slow, trade="buy", df_price=None,
                signal="entry", price="open"):
        """
        A function to generate entry and exit signals individually based on two
        signals crossing one another. The direction in which the cross is
        evaluated is defined by the `trade` value ('buy' or 'sell')

        Parameters
        ----------
        df_sys : pandas.core.frame.DataFrame
            A pandas dataframe indexed by timestamp at consisten intervals
            containing two columns each containing a signal's values.
        fast : str
            The column label for the signal defined by a short time frame
            moving average.
        slow : str
            The column label for the signals defined by a long timeframe
            moving average.
        trade : {'buy', 'sell'}
            The trade directions against which the signal crosses should be
            evaluated against.
        df_price : pandas.core.frame.DataFrame
            The dataframe containing the entry or exit price that should be
            matched against the given timestamp directly following the session
            in which the signal cross occured.
        signal : {'entry', 'exit'}
            Whether to generate price points for a trades entry or exit.
        price : str
            The column label for the chose entry or exit price.

        Returns
        -------
        pandas.core.frame.DataFrame
            A dataframe with a series of entry or exit prices that are
            generated by two signals crossing one another.

        Notes
        -----
        Optimisations yield the following improvements:
        1. 1min 28s ± 5.46 s per loop (mean ± std. dev. of 7 runs, 1 loop each)
        2. 53.4 s ± 1.12 s per loop (mean ± std. dev. of 7 runs, 1 loop each)
        3. 10.8 s ± 400 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
        """
        if trade == "buy":
            df_sys.eval(f"sys = {fast} > {slow}", inplace=True)
        elif trade == "sell":
            df_sys.eval(f"sys = {fast} < {slow}", inplace=True)

        df_sys["prev_sys"] = df_sys["sys"].shift(2)
        df_sys["curr_sys"] = df_sys["sys"].shift(1)

        if signal == "entry":
            df_sys[signal] = pd.eval(
                "(df_sys.curr_sys == 1) & (df_sys.prev_sys == 0)")
        elif signal == "exit":
            df_sys[signal] = pd.eval(
                "(df_sys.curr_sys == 0) & (df_sys.prev_sys == 1)")

        df_sys.index.rename("timestamp", inplace=True)
        en_ex_prep = df_sys[
            df_sys[signal] == True][signal].copy().reset_index()
        del df_sys

        # datetime column label differs due to different setups.
        en_ex_price = en_ex_prep.merge(
            df_price[price], how="left", left_on="timestamp",
            right_index=True, validate="1:1")

        s = en_ex_price.rename(
            columns={
                "timestamp": f"{signal}_dt", f"{price}": f"{signal}_price",
                f"{signal}": f"{signal}_type"})

        return s

    def _stop_loss_by_limit(self, row, pips=.0, exp=3):
        """
        A function to define the stop loss limit a given pip-distance from
        the trade's entry price.

        Parameters
        ----------
        row : pandas.core.Series
            A pandas Series parsed via the built-in pandas.DataFrame.apply
            method. The row will contain values index by column labels
            'entry_type' and 'open'
        pips : float
            A float value representing the pprice difference the stop loss is
            set away from the 'open' price.
        exp : int
            A integer that defines the number of decimal points the stop loss
            value should be rounded to. Yen pairs are rounded to 3 decimal
            places while all other tickers should be rounded to 5 decimal
            places.

        Returns
        -------
        decimal.Decimal
            The stop loss limit.
        "exit"
            If the trade is no longer live.
        """
        if row["entry_type"] is True:
            price = Decimal(str(row["open"]))
            limit = price + Decimal(str(pips))
            return limit.quantize(
                Decimal(f".{'1'.zfill(exp)}"), rounding=ROUND_HALF_EVEN)

        elif row["exit_type"] is True:
            return "exit"

    def _stop_loss_by_atr(self, row, multiplier, trade, exp=3):
        """
        A function to calculate a trailing stop loss for each session within a
        trade. Stop loss is defined x ATR values away from the current open,
        whenever the ticker moves towards the take profit target.

        Parameters
        ----------
        row : pandas.core.Series
            A pandas Series parsed via the built-in pandas.DataFrame.apply
            method. The row will contain values index by column labels
            'set_stop_loss', 'ATR', 'open', 'close' and 'prev_close'.
        multiplier : int
            An positive integer that will multiply the ATR to generate the
            price difference between the stop and the open.
        trade : str {"buy", "sell"}
            The trade direction that is being evaluated by the system.
        exp : int
            A integer that defines the number of decimal points the stop loss
            value should be rounded to. Yen pairs are rounded to 3 decimal
            places while all other tickers should be rounded to 5 decimal
            places.

        Returns
        -------
        float
            The new stop loss value for the given session, or null if the
            ticker moved away from the take profit target. A null value will
            be forward filled by the nearest preceding stop loss price value.
        "exit"
            If the trade is no longer live.
        """
        if isinstance(row["stop_loss_by_limit"], Decimal):
            if trade == "buy":
                if row["prev_close_1"] > row["prev_close_2"] or\
                  row["entry_type"] is True:
                    stop = (Decimal(str(row["open_x"])) +
                            (Decimal(str(row["ATR"])) *
                            Decimal(str(-multiplier)))).quantize(
                                Decimal(f".{'1'.zfill(exp)}"),
                                rounding=ROUND_HALF_EVEN)
                else:
                    stop = np.nan
            elif trade == "sell":
                if row["prev_close_1"] < row["prev_close_2"] or\
                  row["entry_type"] is True:
                    stop = (Decimal(str(row["open_x"])) +
                            (Decimal(str(row["ATR"])) *
                            Decimal(str(multiplier)))).quantize(
                                Decimal(f".{'1'.zfill(exp)}"),
                                rounding=ROUND_HALF_EVEN)
                else:
                    stop = np.nan
            return stop
        else:
            return "exit"

    def _signal_stop_loss(self, row, target, trade):
        """
        A function to catch if/when a ticker crosses the stop loss limit
        while the trade is live. Once the stop loss is crossed a new exit price
        will be recorded for the given trade, overwritting the system's default
        exit price.

        Parameters
        ----------
        row : pandas.core.Series
            A pandas Series parsed via the built-in pandas.DataFrame.apply
            method. The row will contain values index by column labels
            'entry_low' or 'exit_high' and the target column which is almost
            always the set stop loss limit.
        target : str
            A string value corresponding to the column label against which the
            threshold, e.g. stop loss value, is index against in the parsed
            row.
        trade : str {"buy", "sell"}
            The trade direction that is being evaluated by the system.

        Returns
        -------
        boolean
            True or False is used to signify the trade should exit at that
            timestamp.
        """
        if isinstance(row[target], Decimal):
            if trade == "buy" and float(row["exit_low"]) < float(row[target]):
                return True
            elif trade == "sell" and float(row["exit_high"]) > float(
              row[target]):
                return True
        else:
            return False

    def _generate_trades(self, df):
        """
        A function to generate trade signals based on a system's entry and exit
        as well as stop loss threshold.

        Parameters
        ----------
        df : pandas.core.frame.DataFrame
            A pandas dataframe containing columns with entry, exit and stop
            loss values.

        Returns
        -------
        pandas.core.DataFrame
            A pandas dataframe with entry and exit prices and timestamps on
            corresponding rows to represent a trade.
        """
        d = []
        en = False
        signal_data = {}
        stop_ind = 4
        for col in df.columns:
            if "stop_loss_by_" in col:
                stop_ind = list(df.columns).index(col) + 1

        for row in df.itertuples():
            if row[1] is True and en is False:
                signal_data["entry_datetime"] = row[0]
                signal_data["entry_price"] = row[2]
                signal_data["stop_loss"] = row[stop_ind]
                en = True
            elif row[6] is True and en is True:
                signal_data["exit_datetime"] = row[0]
                signal_data["exit_price"] = row[5]
                d.append(copy.deepcopy(signal_data))
                en = False
            elif row[3] is True and en is True:
                signal_data["exit_datetime"] = row[0]
                signal_data["exit_price"] = row[4]
                d.append(copy.deepcopy(signal_data))
                en = False

        return pd.DataFrame(d)


def iky_cat(row):
    """
    To categorise the order in which ichimoku signal lines present with respect
    to each other.
    """
    ls = list(row.sort_values().index)
    cat = "".join(ls)
    return cat


if __name__ == "__main__":
    """
    python htp/analyse/evaluate.py data/sma_3_6.csv
    """

    import re
    data = pd.read_csv(sys.argv[1], header=0, names=["entry", "exit"],
                       index_col=0, parse_dates=True)
    entry_exit = signal_cross(data, data.columns[0], data.columns[1])
    sf = "entry_exit.csv".format()
    try:
        fn = "{0}_{1}".format(re.search(r"\/(.*?)\.csv", sys.argv[1]).group(1),
                              sf)
    except AttributeError:
        fn = sf
    entry_exit.to_csv("data/{0}".format(fn))
