"""Module used to evaluate trade signals generated from analysis."""
import sys
import copy
import numpy as np
import pandas as pd
from tqdm import tqdm
from loguru import logger


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
        A dataframe posessing two columns, indexed by timestamp. Both columns
        contain values that define a standalone signal respectively. These
        signals will be assessed to cross, thereby establishing entry and exit
        actions.

    fast : str
        The column label for the faster moving signal column in the df_sys
        dataframe.

    slow : str
        The column label for the slower moving signal column in the df_sys
        dataframe.

    trade : {"buy", "sell"}
        The trade direction the system will be assessed against.

    diff_SL : float
        The number of pips the default stop loss will be established away from
        the trade entry price.

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

    sys_SL : pandas.core.frame.DataFrame
        A raw dataset from which the entry and exit signals generated by a
        system are appropriately matched to corresponding trades.

    SL_low : pandas.core.frame.DataFrame
        A raw dataset from which the entry and exit signals generated by a
        system are appropriately matched to corresponding trades and be
        adjusted to a set or trailing stop loss.
    """

    def __init__(self, df_mid, df_entry, df_exit, df_sys, fast, slow,
                 trade="buy", diff_SL=-0.5):

        self.df_mid = df_mid
        self.df_entry = df_entry
        self.df_exit = df_exit

        # Checked against signal_cross method doctest (amended to M15).
        self.sys_en = self._signal(
            df_sys, fast, slow, trade=trade, df_price=df_entry)
        self.sys_ex = self._signal(
            df_sys, fast, slow, trade=trade, df_price=df_exit, signal="exit",
            price="close")

        # Checked to ensure no data is leaked in transformations.
        sys_entry = df_mid.merge(
            self.sys_en, how="left", left_index=True, right_on="entry_dt",
            validate="1:1")
        sys_entry.set_index("entry_dt", inplace=True)
        sys_entry_exit = sys_entry.merge(
            self.sys_ex, how="left", left_index=True, right_on="exit_dt",
            validate="1:1")
        sys_entry_exit.set_index("exit_dt", inplace=True)

        # Checked to ensure no data is leaked in transformations.
        sys_entry_exit["set_SL"] = sys_entry_exit.apply(self._set_SL,
                                                        SL=diff_SL, axis=1)
        set_SL_price = sys_entry_exit["set_SL"].fillna(method="ffill")
        sys_entry_exit.drop("set_SL", axis=1, inplace=True)
        self.sys_SL = sys_entry_exit.merge(
            set_SL_price, how="left", left_index=True, right_index=True,
            validate="1:1")

        df_exit.rename(columns={"low": "exit_low"}, inplace=True)
        self.SL_low = self.sys_SL.merge(
            df_exit, how="left", left_index=True, right_index=True,
            validate="1:1")

    @classmethod
    def sys_signals(cls, *args, **kwargs):
        """
        Fuction to return trades with entry and exit signals derived from a
        given SMA cross system.

        Examples
        --------
        >>> import copy
        >>> from htp import runner
        >>> from htp.api import oanda
        >>> from htp.analyse import indicator
        >>> func = oanda.Candles.to_df
        >>> instrument = "AUD_JPY"
        >>> qP = {"from": "2012-01-01 17:00:00",
        ...       "to": "2012-06-27 17:00:00",
        ...       "granularity": "H1", "price": "M"}
        >>> data_mid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP)
        >>> qP_ask = copy.deepcopy(qP)
        >>> qP_ask["price"] = "A"
        >>> data_ask = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_ask)
        >>> qP_bid = copy.deepcopy(qP)
        >>> qP_bid["price"] = "B"
        >>> data_bid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_bid)
        >>> data_prop = indicator.Momentum(data_mid)
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.sys_signals(data_mid, data_ask, data_bid, sma_6_24,
        ...                     "close_sma_6", "close_sma_24", trade="buy",
        ...                     diff_SL=-0.2).head()
               entry_datetime  entry_price       exit_datetime  exit_price
        0 2012-01-02 23:00:00       78.795 2012-01-04 05:00:00      79.463
        1 2012-01-04 20:00:00       79.561 2012-01-05 03:00:00      79.234
        2 2012-01-05 21:00:00       79.296 2012-01-06 07:00:00      78.982
        3 2012-01-09 12:00:00       78.553 2012-01-11 01:00:00      79.070
        4 2012-01-11 10:00:00       79.425 2012-01-11 16:00:00      79.154
        """
        n = cls(*args, **kwargs)
        d = []
        en = False
        signal_data = {}

        logger.info(
            f"Generating signals from {n.sys_SL.iloc[0].name} to "
            f"{n.sys_SL.iloc[-1].name}\n")

        for row in tqdm(n.sys_SL.itertuples()):

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
    def set_stop_signals(cls, *args, **kwargs):
        """
        Fuction to return trades with entry signals derived from a given
        SMA cross system, and exit signals set by either the system or, if
        crossed, a stop loss limit x pips from the entry price.

        Examples
        --------
        >>> import copy
        >>> from htp import runner
        >>> from htp.api import oanda
        >>> from htp.analyse import indicator
        >>> func = oanda.Candles.to_df
        >>> instrument = "AUD_JPY"
        >>> qP = {"from": "2012-01-01 17:00:00",
        ...       "to": "2012-06-27 17:00:00",
        ...       "granularity": "H1", "price": "M"}
        >>> data_mid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP)
        >>> qP_ask = copy.deepcopy(qP)
        >>> qP_ask["price"] = "A"
        >>> data_ask = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_ask)
        >>> qP_bid = copy.deepcopy(qP)
        >>> qP_bid["price"] = "B"
        >>> data_bid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_bid)
        >>> data_prop = indicator.Momentum(data_mid)
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.set_stop_signals(
        ...     data_mid, data_ask, data_bid, sma_6_24, "close_sma_6",
        ...     "close_sma_24", trade="buy", diff_SL=-0.2).head()
               entry_datetime  entry_price       exit_datetime  exit_price
        0 2012-01-02 23:00:00       78.795 2012-01-04 05:00:00      79.463
        1 2012-01-04 20:00:00       79.561 2012-01-04 23:00:00      79.350
        2 2012-01-05 21:00:00       79.296 2012-01-05 22:00:00      79.086
        3 2012-01-09 12:00:00       78.553 2012-01-11 01:00:00      79.070
        4 2012-01-11 10:00:00       79.425 2012-01-11 11:00:00      79.216
        """
        n = cls(*args, **kwargs)
        n.SL_low["set_SL_exit_type"] = n.SL_low.apply(
            n._signal_SL, args=("set_SL",), axis=1)

        return n._gen_signal(n.SL_low, "set_SL_exit_type", "set_SL")

    @classmethod
    def atr_stop_signals(cls, df_prop, *args, ATR_multiplier=-3, **kwargs):
        """
        Fuction to return trades with entry signals derived from a given
        SMA cross system, and exit signals set by either the system or, if
        crossed, a stop loss limit x * ATR from the entry price.

        Examples
        --------
        >>> import copy
        >>> from htp import runner
        >>> from htp.api import oanda
        >>> from htp.analyse import indicator
        >>> func = oanda.Candles.to_df
        >>> instrument = "AUD_JPY"
        >>> qP = {"from": "2012-01-01 17:00:00",
        ...       "to": "2012-06-27 17:00:00",
        ...       "granularity": "H1", "price": "M"}
        >>> data_mid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP)
        >>> qP_ask = copy.deepcopy(qP)
        >>> qP_ask["price"] = "A"
        >>> data_ask = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_ask)
        >>> qP_bid = copy.deepcopy(qP)
        >>> qP_bid["price"] = "B"
        >>> data_bid = runner.setup(
        ...     func=func, instrument=instrument, queryParameters=qP_bid)
        >>> data_prop = indicator.Momentum(data_mid)
        >>> sma_6 = indicator.smooth_moving_average(data_mid, period=6)
        >>> sma_6_24 = indicator.smooth_moving_average(
        ...     data_mid, df2=sma_6, period=24, concat=True)
        >>> Signals.atr_stop_signals(
        ...     data_prop.atr, data_mid, data_ask, data_bid, sma_6_24,
        ...     "close_sma_6", "close_sma_24", ATR_multiplier=-2,
        ...     trade="buy").head()
               entry_datetime  entry_price       exit_datetime  exit_price
        0 2012-01-02 23:00:00       78.795 2012-01-04 02:00:00   79.196604
        1 2012-01-04 20:00:00       79.561 2012-01-05 00:00:00   79.220111
        2 2012-01-05 21:00:00       79.296 2012-01-06 07:00:00   78.982000
        3 2012-01-09 12:00:00       78.553 2012-01-11 01:00:00   79.070000
        4 2012-01-11 10:00:00       79.425 2012-01-11 16:00:00   79.154000
        """
        n = cls(*args, **kwargs)
        # ATR values shifted for calculations, i.e. use previous sessions's ATR
        # to define current session's SL.
        atr_shift = df_prop["ATR"].shift(1)
        set_ATR_SL = n.SL_low.merge(
            atr_shift, how="left", left_index=True, right_index=True,
            validate="1:1")

        set_ATR_SL["prev_close"] = set_ATR_SL["close_x"].shift(1)
        set_ATR_SL["ATR_SL"] = set_ATR_SL.apply(
            n._set_ATR_SL, args=(ATR_multiplier,), axis=1)
        ATR_SL_price = set_ATR_SL["ATR_SL"].fillna(method="ffill")
        set_ATR_SL.drop("ATR_SL", axis=1, inplace=True)
        set_ATR_SL = set_ATR_SL.merge(
            ATR_SL_price, how="left", left_index=True, right_index=True,
            validate="1:1")
        set_ATR_SL["set_ATR_SL_exit_type"] = set_ATR_SL.apply(
            n._signal_SL, args=("ATR_SL",), axis=1)

        return n._gen_signal(set_ATR_SL, "set_ATR_SL_exit_type", "ATR_SL")

    def _signal(self, df_sys, fast, slow, trade="buy", df_price=None,
                signal="entry", price="open"):
        """
        1. 1min 28s ± 5.46 s per loop (mean ± std. dev. of 7 runs, 1 loop each)
        2. 53.4 s ± 1.12 s per loop (mean ± std. dev. of 7 runs, 1 loop each)
        3. 10.8 s ± 400 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
        """
        if trade == "buy":
            # system = "{} > {}".format(fast, slow)
            df_sys.eval(f"sys = {fast} > {slow}", inplace=True)

        # elif trade == "sell":
            # system = "{} < {}".format(fast, slow)
            # en_ex = df_sys.apply(
            #     lambda x: signal if x[fast] < x[slow] else False, axis=1
            #     ).rename(system).to_frame()

        df_sys["prev_sys"] = df_sys["sys"].shift(2)
        df_sys["curr_sys"] = df_sys["sys"].shift(1)

        if signal == "entry":
            df_sys[signal] = pd.eval(
                "(df_sys.curr_sys == 1) & (df_sys.prev_sys == 0)")
        elif signal == "exit":
            df_sys[signal] = pd.eval(
                "(df_sys.curr_sys == 0) & (df_sys.prev_sys == 1)")

        en_ex_prep = df_sys[
            df_sys[signal] == True][signal].copy().reset_index()
        del df_sys

        en_ex_price = en_ex_prep.merge(
            df_price[price], how="left", left_on="timestamp",
            right_index=True, validate="1:1")

        s = en_ex_price.rename(
            columns={
                "timestamp": f"{signal}_dt", f"{price}": f"{signal}_price",
                f"{signal}": f"{signal}_type"})

        return s

    def _entry_exit(self, row, action):

        if action == "entry":
            if row["prev"] is False and row["curr"] == action:
                return action

        elif action == "exit":
            if row["prev"] == action and row["curr"] is False:
                return action

    def _set_SL(self, row, SL=.0):

        if row["entry_type"] is True:
            limit = float(row["open"]) + SL
            return limit

        elif row["exit_type"] is True:
            return "exit"

    def _set_ATR_SL(self, row, multiplier):

        if isinstance(row["set_SL"], float):
            if row["close_x"] > row["prev_close"]:
                return float(row["open_x"]) + (row["ATR"] * multiplier)
            else:
                return np.nan
        else:
            return "exit"

    def _signal_SL(self, row, target):

        try:
            if float(row["exit_low"]) < row[target]:
                return True  # "exit"
        except TypeError:
            return False  # np.nan
        else:
            return False  # np.nan

    def _gen_signal(self, df, target_type, target_price):

        d = []
        en = False
        signal_data = {}

        # for row in df.iterrows():
        for row in df.itertuples():

            # if row[1]["entry_type"] == "entry" and en is False:
            if row[5] is True and en is False:
                signal_data["entry_datetime"] = row[0]
                signal_data["entry_price"] = row[6]  # ["entry_price"]
                en = True

            # elif row[1][target_type] == "exit" and en is True:
            elif row[14] is True and en is True:
                signal_data["exit_datetime"] = row[0]
                signal_data["exit_price"] = row[9]  # [target_price]
                d.append(copy.deepcopy(signal_data))
                en = False

            # elif row[1]["exit_type"] == "exit" and en is True:
            elif row[7] is True and en is True:
                signal_data["exit_datetime"] = row[0]
                signal_data["exit_price"] = row[8]  # ["exit_price"]
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

    import sys
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
