"""Module for calculating position sizes."""

import copy
# import datetime
import functools
import numpy as np
import pandas as pd
from tqdm import tqdm
from pprint import pprint
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_DOWN, InvalidOperation


ticker_conversion_pairs = {
    "AUD_CAD": "AUD_CAD", "NZD_USD": "AUD_USD", "NZD_JPY": "AUD_JPY",
    "AUD_JPY": "AUD_JPY", "AUD_NZD": "AUD_NZD", "AUD_USD": "AUD_USD",
    "USD_JPY": "AUD_JPY", "USD_CHF": "AUD_CHF", "GBP_CHF": "AUD_CHF",
    "NZD_CAD": "AUD_CAD", "CAD_JPY": "AUD_JPY", "USD_CAD": "AUD_CAD",
    "EUR_GBP": "GBP_AUD", "EUR_CHF": "AUD_CHF", "EUR_JPY": "AUD_JPY",
    "GBP_JPY": "AUD_JPY", "GBP_USD": "AUD_USD", "EUR_USD": "AUD_USD",
    "EUR_NZD": "AUD_NZD", "GBP_CAD": "AUD_CAD", "EUR_CAD": "AUD_CAD",
    "CHF_JPY": "AUD_JPY", "GBP_AUD": "GBP_AUD", "EUR_AUD": "EUR_AUD",
    "GBP_NZD": "AUD_NZD", "USB10Y_USD": "AUD_USD", "UK10YB_GBP": "GBP_AUD",
    "AU200_AUD": "AU200_AUD", "BCO_USD": "AUD_USD", "DE10YB_EUR": "EUR_AUD",
    "XCU_USD": "AUD_USD", "CORN_USD": "AUD_USD", "EU50_EUR": "EUR_AUD",
    "FR40_EUR": "EUR_AUD", "DE30_EUR": "EUR_AUD", "XAU_AUD": "XAU_AUD",
    "IN50_USD": "AUD_USD", "JP225_USD": "AUD_USD", "NATGAS_USD": "AUD_USD",
    "XAG_AUD": "XAG_AUD", "SOYBN_USD": "AUD_USD", "SUGAR_USD": "AUD_USD",
    "SPX500_USD": "AUD_USD", "NAS100_USD": "AUD_USD", "WTICO_USD": "AUD_USD",
    "WHEAT_USD": "AUD_USD"}


def std_dec(func):
    """
    A decorator to convert all keyword arguments to Decimal objects in the
    wrapped function.

    The wrapped function is one of four position size calculators, chosen
    depending on the context of the target ticker, and account currency
    denomination.

    Parameters
    ----------
    func
        The position size calculator whose inputs will be standardised as
        Decimal objects.

    Returns
    -------
    decimal.Decimal
        A position size in arbitary units defined as a Decimal object.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        The internal wrapper that actions input conversion to Decimal objects.

        Parameters
        ----------
        kwargs
            Keyword arguments defined within the wrapped function.

        Returns
        -------
        decimal.Decimal
            A position size in arbitary units defined as a Decimal object.
        """
        decimal_kwargs = {}
        for kwarg in kwargs:
            try:
                decimal_kwargs[kwarg] = Decimal(kwargs[kwarg])
            except InvalidOperation:
                decimal_kwargs[kwarg] = kwargs[kwarg]

        return func(*args, **decimal_kwargs)

    return wrapper

# For currency pairs displayed to 4 decimal places, one pip = 0.0001
# Yen-based currency pairs are an exception, and are displayed to only two
# decimal places (0.01)
# KNOWN_RATIO_OTHER = (1, 0.0001)
# KNOWN_RATIO_YEN = (1, 0.01)


class Position:

    def __init__(self, ticker, ACC_AMOUNT, RISK_PERC, *args, **kwargs):
        """
        A class that contains the different calculators required to generate a
        position size based off the amount of funds in an account and the
        percentage of those funds, as a decimal, that will be risked.

        Parameters
        ----------
        ACC_AMOUNT : float
            The sum value of the account from which funds will be used to place
            the trade.
        RISK_PERC : float
            The percentage of the account in decimal format that will be risked
            on this trade.

        Attributes
        ----------
        ticker : str
            The symbol label being traded.
        MAX_RISK_ACC_CURR : decimal.Decimal
            The maximum amount in the account denomination that is being risked
            on the given trade.
        KNOWN_RATIO : float
            The known unit to pip ratio for the traded ticker.
        """
        self.ticker = ticker
        self.MAX_RISK_ACC_CURR = Decimal(ACC_AMOUNT) * Decimal(RISK_PERC)
        self.KNOWN_RATIO = 0.0001
        if ticker.split("_")[1] == "JPY":
            self.KNOWN_RATIO = 0.01

    def calculator(cls, *args, acc_denomination="AUD", **kwargs):
        """
        A function to select the appropriate position size calculator based on
        ticker traded and account denomination.

        Parameters
        ----------
        acc_denomination : str {'AUD'}
            The currency of funds held in the trading account.

        Returns
        -------
        The appropriate class function to calculate position size depending
        on the symbol that is to be traded.
        """
        ticker = cls.ticker

        if acc_denomination in ticker.split("_")[1]:
            return cls.acc_is_counter_traded

        elif acc_denomination in ticker.split("_")[0]:
            return cls.acc_is_base_traded

        elif acc_denomination in ticker_conversion_pairs[ticker].split("_")[1]:
            return cls.acc_is_counter_conversion

        elif acc_denomination in ticker_conversion_pairs[ticker].split("_")[0]:
            return cls.acc_is_base_conversion

    @classmethod
    def size(cls, *args, CONV=None, **kwargs):
        """
        General function that selects the appropriate calculator based on the
        ticker traded and the account denomination before enacting that
        function to calculate position size.
        """
        calc = cls(*args, **kwargs)
        func = calc.calculator()
        return func(*args, CONV=CONV, **kwargs)

    @classmethod
    def acc_is_counter_traded(cls, *args, STOP=100, **kwargs):
        """
        A position size calculator to use when the account currency
        denomination is the same as the counter currency (denominator) of the
        traded ticker.

        Paramaters
        ----------
        STOP : float
            The number of pips between the entry price and the stop loss exit
            price.

        Returns
        ------
        float
            The trade position size in arbitary units.

        Examples
        --------
        >>> pos_size = Position.acc_is_counter_traded(AUD_JPY, 1000, 0.01)
        >>> print(pos_size)
        1000
        """
        risk = cls(*args, **kwargs)

        VALUE_PER_PIP = risk.MAX_RISK_ACC_CURR / Decimal(STOP)

        POSITION_SIZE = VALUE_PER_PIP * (Decimal(1) /
                                         Decimal(risk.KNOWN_RATIO))

        return POSITION_SIZE.quantize(Decimal(1.), rounding=ROUND_DOWN)

    @classmethod
    def acc_is_base_traded(cls, *args, STOP=100, CONV=1., **kwargs):
        """
        A position size calculator to use when the account currency
        denomination is the same as the base currency (nominator) of the traded
        ticker.

        Parameters
        ----------
        STOP : float
            The number of pips between the entry price and the stop loss exit
            price.
        CONV : float
            The asking price for the traded ticker at present.

        Returns
        ------
        float
            The trade position size in arbitary units.

        Examples
        --------
        >>> pos_size = Position.acc_is_base_traded(
        ...     "AUD_JPY", 1000, 0.01, STOP=50, CONV=78.5)
        >>> print(pos_size)
        1570
        """
        risk = cls(*args, **kwargs)

        MAX_RISK_CNT_CURR = risk.MAX_RISK_ACC_CURR * Decimal(CONV)

        VALUE_PER_PIP = MAX_RISK_CNT_CURR / Decimal(STOP)

        POSITION_SIZE = VALUE_PER_PIP * (Decimal(1) /
                                         Decimal(risk.KNOWN_RATIO))

        return POSITION_SIZE.quantize(Decimal(1.), rounding=ROUND_DOWN)

    @classmethod
    def acc_is_counter_conversion(cls, *args, STOP=100, CONV=1., **kwargs):
        """
        A position size calculator to use when the account currency
        denomination is the same as the counter currency (denominator) of the
        conversion pair.

        The conversion pair is used to convert the risk calculated in the
        account currency, across to the target pair's counter currency.

        Parameters
        ----------
        STOP : float
            The number of pips between the entry price and the stop loss exit
            price.
        CONV : float
            The bid price for the conversion ticker at present.

        Returns
        ------
        float
            The trade position size in arbitary units.

        Examples
        --------
        >>> # CONV_ASK is current GBP_AUD bid price
        >>> pos_size = Position.acc_is_counter_conversion(
        ...     "EUR_GBP", 1000, 0.01, STOP=50, CONV=1.82)
        >>> print(pos_size)
        1098
        """
        risk = cls(*args, **kwargs)

        MAX_RISK_TARGET_CNT = risk.MAX_RISK_ACC_CURR * \
            (Decimal(1) / Decimal(CONV))

        VALUE_PER_PIP = MAX_RISK_TARGET_CNT / Decimal(STOP)

        POSITION_SIZE = VALUE_PER_PIP * (Decimal(1) /
                                         Decimal(risk.KNOWN_RATIO))

        return POSITION_SIZE.quantize(Decimal(1.), rounding=ROUND_DOWN)

    @classmethod
    def acc_is_base_conversion(cls, *args, STOP=100, CONV=1., **kwargs):
        """
        A position size calculator to use when the account currency
        denomination is the same as the base currency (nominator) of the
        conversion pair.

        The conversion pair is used to convert the risk calculated in the
        account currency, across to the target pair's counter currency.

        Parameters
        ----------
        CONV : float
            The asking price for the conversion ticker at present.
        STOP : float
            The number of pips between the entry price and the stop loss exit
            price.

        Returns
        ------
        float
            The trade position size in arbitary units.

        Examples
        --------
        >>> # CONV_ASK is the current AUD_JPY ask price
        >>> pos_size = Position.acc_is_base_conversion(
        ...     "CAD_JPY", 1000, 0.01, STOP=50, CONV_ASK=86.25)
        >>> print(pos_size)
        1725
        """
        risk = cls(*args, **kwargs)

        MAX_RISK_TARGET_CNT = risk.MAX_RISK_ACC_CURR * Decimal(CONV)

        VALUE_PER_PIP = MAX_RISK_TARGET_CNT / Decimal(STOP)

        POSITION_SIZE = VALUE_PER_PIP * (Decimal(1) /
                                         Decimal(risk.KNOWN_RATIO))

        return POSITION_SIZE.quantize(Decimal(1.), rounding=ROUND_DOWN)


@std_dec
def profit_loss(ticker, ENTRY=1.0, EXIT=1.1, POS_SIZE=2500, CONV=1.0,
                TRADE="buy"):
    """
    Profit and loss calculator.

    Parameters
    ----------
    ticker : str
        Symbol being traded.
    ENTRY : float
        The trade's entry price.
    EXIT : float
        The trade's exit price.
    POS_SIZE : int
        The trade's position size in units.
    CONV : float
        The price at time of exit for the conversion pair. The conversion pair
        is defined by the account denomination against the traded pair counter
        currency.
    TRADE : {'buy', 'sell'}
        Informs on trade direction for profit to be properly recognised.

    Returns
    -------
    float
        The trade's value in the account denomination currency.

    Examples
    --------
    >>> profit_loss_amount = profit_loss(
    ...     "AUD_JPY", ENTRY=75, EXIT=70, POS_SIZE=1500, CONV=70, TRADE="sell")
    >>> print(profit_loss_amount)
    107.14
    >>> profit_loss_amount = profit_loss(
    ...     "EUR_GBP", ENTRY=0.89, EXIT=0.92, POS_SIZE=1098, CONV=1.82)
    >>> print(profit_loss_amount)
    59.95
    """
    PIP_DELTA = EXIT - ENTRY
    if TRADE == "sell":
        PIP_DELTA = -PIP_DELTA

    # Invert the conversion rate if the account denomination is not the counter
    # currency, i.e. the base currency, in the conversion pair, composed of the
    # traded counter currency against the account currency.
    if "AUD" in ticker and "AUD" not in ticker.split("_")[1]:
        CONV = (1 / CONV)
    elif "AUD" in ticker_conversion_pairs[ticker] and\
            "AUD" not in ticker_conversion_pairs[ticker].split("_")[1]:
        CONV = (1 / CONV)
    else:
        CONV = CONV

    CURR_DELTA = PIP_DELTA * CONV

    ACC_AMOUNT = CURR_DELTA * POS_SIZE

    return ACC_AMOUNT.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def count(trades, ticker, amount, RISK_PERC, trade_type, conv=False):
    """
    Function to calculate trade information: P/L Pips, P/L AUD, Position Size,
    Realised P/L.

    Parameters
    ----------
    trades : pandas.core.frame.DataFrame
        A pandas dataframe that contains entry, exit and conversion prices as
        as well as stop loss (pips) in respective columns, with each row
        representing an individual trade.

    Returns
    -------
    pandas.core.frame.DataFrame
        The original parsed dataframe with appended columns contain the
        calculated information respective to each trade.
    """
    AMOUNT = amount

    if "JPY" in ticker:
        KNOWN_RATIO = (100, 0.01)
    else:
        KNOWN_RATIO = (10000, 0.0001)

    coeff = {'sell': -1, 'buy': 1}

    trades["PL_PIPS"] = trades.apply(
        lambda x: (float(
            ((Decimal(x["exit_price"]) - Decimal(x["entry_price"]))
             * Decimal(f"{KNOWN_RATIO[0]}") * coeff[trade_type]).quantize(
                Decimal(".1")))), axis=1)

    d_pos_size = {}
    stop = list(trades.columns).index('stop_loss') + 1
    exit = list(trades.columns).index('exit_price') + 1
    entry = list(trades.columns).index('entry_price') + 1
    entry_dt = list(trades.columns).index('entry_datetime') + 1
    if conv:
        conv_entry = list(trades.columns).index('conv_entry_price') + 1
        conv_exit = list(trades.columns).index('conv_exit_price') + 1
    else:
        conv_entry = None
        conv_exit = None

    for trade in trades.itertuples():
        size = Position.size(
            ticker, AMOUNT, RISK_PERC, CONV=trade[conv_entry],
            STOP=trade[stop])
        profit = profit_loss(
            ticker, ENTRY=trade[entry], EXIT=trade[exit], POS_SIZE=size,
            CONV=trade[conv_exit], TRADE=trade_type)
        AMOUNT += profit
        d_pos_size[trade[entry_dt]] = {
            "POS_SIZE": int(size), "PL_AUD": float(profit), "PL_REALISED":
            float(AMOUNT)}
    counting = pd.DataFrame.from_dict(d_pos_size, orient="index")
    entry_exit_complete = trades.merge(
        counting, how="left", left_on="entry_datetime", right_index=True,
        validate="1:1")

    return entry_exit_complete


def count_unrealised(data_mid, trades, ticker, amount, RISK_PERC, CONV):
    """
    Function to calculate trade information: P/L Pips, P/L AUD, Position Size,
    Realised P/L.

    Parameters
    ----------
    trades : pandas.core.frame.DataFrame
        A pandas dataframe that contains entry, exit, stop loss (pips) and
        conversion prices in respective columns, with each row representing an
        individual trade.

    Returns
    -------
    pandas.core.frame.DataFrame
        The original parsed dataframe with appended columns contain the
        calculated information respective to each trade.
    """
    AMOUNT = amount
    trades["P/L PIPS"] = trades.apply(
        lambda x: (
            (Decimal(x["exit_price"]) - Decimal(x["entry_price"]))
            * Decimal("100")).quantize(Decimal(".1")), axis=1)
    unrealised = []
    # {"entry_datetime": Timestamp, "entry_price": float, "exit_datetime":
    #   timestamp, "exit_price": float, "POS_SIZE": size, "P/L PIPS": float,
    #   "P/L AUD": float, "margin": float}
    d = {}
    for timestamp in tqdm(data_mid.index):
        pips = []
        profit = []
        info = []
        margin = []
        for i in range(len(unrealised)):
            if timestamp == unrealised[i]["exit_datetime"]:
                trade = unrealised[i]  # .pop(i)
                # print(trade)
                margin.append(trade["margin"])
                pips.append(trade["P/L PIPS"])
                profit.append(trade["P/L AUD"])
                info.append(f"{trade['POS_SIZE']} units on "
                            f"{trade['entry_datetime']} @ "
                            f"{trade['entry_price']} "
                            f"signaled by {trade['label']}")

        if len(pips) > 0:
            if len(info) > 1:
                pprint(info)
            AMOUNT += float((sum(margin) + sum(profit)))
            d[timestamp] = {
                "P/L PIPS": sum(pips), "P/L AUD": sum(profit), "trade_info":
                " ".join(info), "P/L REALISED": AMOUNT}
        else:
            d[timestamp] = {
                "P/L PIPS": np.nan, "P/L AUD": np.nan, "trade_info": np.nan,
                "P/L REALISED": AMOUNT}

        entries = trades.loc[trades["entry_datetime"] == timestamp]
        if len(entries) > 0:
            for i in range(len(entries)):
                trade = entries.iloc[i]
                size = Position.size(
                    ticker, AMOUNT, RISK_PERC, CONV=entries[5],
                    STOP=entries[6])
                profit = profit_loss(
                    ENTRY=trade["entry_price"], EXIT=trade["exit_price"],
                    POS_SIZE=size, CONV=entries[CONV], CNT=0)
                margin = (
                    Decimal(AMOUNT) * Decimal(0.0025)).quantize(Decimal(".01"))
                AMOUNT -= float(margin)
                values = {
                    "entry_datetime": trade["entry_datetime"], "entry_price":
                    Decimal(trade["entry_price"]).quantize(Decimal(".0001")),
                    "exit_datetime": trade["exit_datetime"], "exit_price":
                    Decimal(trade["exit_price"]).quantize(Decimal(".0001")),
                    "POS_SIZE": size, "P/L AUD":
                    profit, "P/L PIPS": trade["P/L PIPS"], "margin": margin,
                    "label": trade["label"]}
                unrealised.append(copy.deepcopy(values))

    counting = pd.DataFrame.from_dict(d, orient="index")
    return counting


def performance_stats(results):
    """
    Function to assess the performance of a given trading system.

    Parameters
    ----------
    results : pandas.core.frame.DataFrame
        The dataframe that contain all trades by a given system, with entry and
        exit timestamps and prices, position size, profit & loss in pips and
        AUD, as well as realised and loss as a cumulative sum over time.

    Returns
    -------
    pandas.core.frame.Data
        A pandas dataframe that outlines the Net Profit, Win %, Loss %, Largest
        Winning Trade, Largest Losing Trade, Average Winning Trade, Average
        Losing Trade, Payoff Ratio per Trade, Average Holding Time per Trade,
        Largest # Consecutive Losses, Average # Consecutive Losses, Trading
        Expectancy.
    """

    stats = {}
    stats["net_profit"] = results.iloc[-1]["PL_REALISED"] - 1000

    stats["win_%"] = Decimal(
        results[results["PL_AUD"] > 0]["PL_AUD"].count() /
        results["PL_AUD"].count() *
        100).quantize(Decimal("0.01"))
    stats["loss_%"] = Decimal(
        results[results["PL_AUD"] < 0]["PL_AUD"].count() /
        results["PL_AUD"].count() *
        100).quantize(Decimal("0.01"))

    stats["win_max"] = results["PL_AUD"].max()
    stats["loss_max"] = results["PL_AUD"].min()

    stats["win_mean"] = Decimal(
        results[results["PL_AUD"] > 0]["PL_AUD"].mean()
        ).quantize(Decimal("0.01"))
    stats["loss_mean"] = Decimal(
        results[results["PL_AUD"] < 0]["PL_AUD"].mean()
        ).quantize(Decimal("0.01"))

    # holding_time = results["exit_datetime"] - results["entry_datetime"]
    # stats["average_holding_time_per_trade"] = str(
    #     datetime.timedelta(seconds=holding_time.mean().seconds))

    cons_loss = 0
    list_cons_loss = []
    for row in results.iterrows():
        if row[1]["PL_AUD"] < 0:
            cons_loss += 1
            if cons_loss == 1:
                list_cons_loss.append(copy.deepcopy(cons_loss))
            else:
                list_cons_loss[-1] = copy.deepcopy(cons_loss)
        elif row[1]["PL_AUD"] >= 0:
            cons_loss = 0

    if len(list_cons_loss) > 0:
        stats["max_cons_loss"] = Decimal(max(list_cons_loss))
        stats["mean_cons_loss"] = Decimal(
            sum(list_cons_loss) / len(list_cons_loss)
            ).quantize(Decimal("1."))

    stats["trading_exp"] = (
        (stats["win_%"] / Decimal("100") * stats["win_mean"]) +
        (stats["loss_%"] / Decimal("100") * stats["loss_mean"])
        ).quantize(Decimal("0.01"))

    return stats
