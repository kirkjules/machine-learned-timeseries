import copy
import numpy as np
import pandas as pd


class Signals:

    def __init__(self, df_mid, df_entry, df_exit, df_sys, fast, slow,
                 trade='buy', stop=0.5, exp=3):
        """
        16.4 ms ± 317 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
        """

        self.trade = trade
        self.close = df_mid.close.to_numpy()
        self.entry = df_entry.open.to_numpy()
        self.exit = df_exit.open.to_numpy()
        self.index = df_mid.index
        self.fast = df_sys[f"{fast}"].to_numpy()
        self.slow = df_sys[f"{slow}"].to_numpy()
        self.stop = abs(stop)
        self.exit_high = df_exit.high.to_numpy()
        self.exit_low = df_exit.low.to_numpy()
        if trade == "buy":
            self.stop = -abs(stop)
            self.raw_signals = self._signal(
                self.fast, self.slow, self.entry, self.exit, self.index,
                self.stop, exp)
        elif trade == 'sell':
            self.raw_signals = self._signal(
                self.slow, self.fast, self.entry, self.exit, self.index,
                self.stop, exp)

    def _signal(self, a, b, p_en, p_ex, dt_index, stop, exp):
        """
        Parameters
        ----------
        a : ndarray
            Smooth moving average that is greater when the trade is on. For
            a 'buy' trade, this is the fast smooth moving average, and for a
            'sell' trade, this is the slow smooth moving average.
        b : ndarray
            Smooth moving average that is lesser when the trade is on. For
            a 'buy' trade, this is the slow smooth moving average, and for a
            'sell' trade, this is the fast smooth moving average.
        p_en : ndarray
            The array containing either the ticker's ask or bid price for a
            session's open. This is the price at which the trade enters. For a
            buy trade, the entry price is the ask, for a sell trade, the entry
            price is the bid.
        p_ex : ndarray
            The array containing either the ticker's ask or bid price for a
            session's open. This is the price at which the trade exits. For a
            buy trade, the exit is the bid, for a sell trade, the exit is the
            ask.
        """
        sys = np.greater(a, b)
        prev_sys = np.roll(sys, 2)
        curr_sys = np.roll(sys, 1)
        en = np.greater(curr_sys, prev_sys)
        ex = np.greater(prev_sys, curr_sys)
        en_p = np.where(en == True, p_en, np.nan)
        ex_p = np.where(ex == True, p_ex, np.nan)

        stop_en = (en == True)
        stop_ex = (ex == True)
        stop_loss = np.full_like(en, np.nan, dtype=np.double)
        stop_loss[stop_en] = p_en[stop_en] + stop
        stop_loss[stop_ex] = -1.0

        s = pd.DataFrame(
            {'entry_type': en, 'entry_price': en_p, 'exit_type': ex,
             'exit_price': ex_p, 'stop_loss_by_limit': stop_loss},
            index=dt_index)
        s['stop_loss_by_limit'].fillna(method="ffill", inplace=True)
        return s

    @classmethod
    def atr_stop_signals(cls, df_prop, *args, multiplier=6.0, **kwargs):
        base = cls(*args, **kwargs)
        en = base.raw_signals.entry_type.to_numpy()
        prev_close_1 = np.roll(base.close, 1)
        prev_close_2 = np.roll(base.close, 2)
        atr = np.roll(df_prop.ATR.to_numpy(), 1)

        # stop loss by atr
        stop_loss_by_atr = np.full_like(base.entry, np.nan, dtype=np.double)
        if base.trade == 'buy':
            stop_loss = np.where(
                np.greater(prev_close_1, prev_close_2) | (en == True),
                base.entry + (atr * -multiplier), np.nan)
        elif base.trade == 'sell':
            stop_loss = np.where(
                np.greater(prev_close_2, prev_close_1) | (en == True),
                base.entry + (atr * multiplier), np.nan)
        stop_loss_by_limit = base.raw_signals.stop_loss_by_limit.to_numpy()
        stop_loss_by_limit[0] = -1.0
        stop_loss_by_limit_true = np.greater(stop_loss_by_limit, 0)
        stop_loss_by_atr[stop_loss_by_limit_true] = stop_loss[
            stop_loss_by_limit_true]
        stop_loss_by_atr[~stop_loss_by_limit_true] = -1.0

        # ffill na
        prev = np.arange(len(stop_loss_by_atr))
        prev[np.isnan(stop_loss_by_atr)] = 0
        prev = np.maximum.accumulate(prev)
        stop_loss_by_atr = stop_loss_by_atr[prev]

        # exit type by atr
        exit_type_by_atr = np.full_like(base.entry, np.nan, dtype=np.double)
        if base.trade == 'buy':
            exit_type = np.greater(stop_loss_by_atr, base.exit_low)
        elif base.trade == 'sell':
            exit_type = np.greater(base.exit_high, stop_loss_by_atr)
        stop_loss_by_atr_true = np.greater(stop_loss_by_atr, 0)
        exit_type_by_atr[stop_loss_by_atr_true] = exit_type[
            stop_loss_by_atr_true]

        en_p = base.raw_signals.entry_price.to_numpy()
        ex = base.raw_signals.exit_type.to_numpy()
        ex_p = base.raw_signals.exit_price.to_numpy()

        df = pd.DataFrame(
            {'entry_type': en, 'entry_price': en_p, 'exit_type': ex,
             'exit_price': ex_p, 'stop_loss_by_atr': stop_loss_by_atr,
             'ex_type_by_atr': exit_type_by_atr},
            index=base.index)

        return base._generate_trades(df)

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

        for row in df.itertuples():
            if row[1] is True and en is False:
                signal_data["entry_datetime"] = row[0]
                signal_data["entry_price"] = row[2]
                signal_data["stop_loss"] = row[5]
                en = True
            elif row[6] == 1 and en is True:
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

        # return np.stack((en, en_p, ex, ex_p,
        #                  stop_loss_by_atr, exit_type_by_atr), axis=-1)
        # 1: "entry_type", 2: "entry_price", 3: "exit_type", 4: "exit_price"
        # 5: "stop_loss_by_ATR", 6: "ex_type_by_ATR"
