"""Module for calculating position sizes."""

import copy
import decimal
import datetime
import functools


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
    def wrapper(**kwargs):
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
            decimal_kwargs[kwarg] = decimal.Decimal(kwargs[kwarg])

        return func(**decimal_kwargs)

    return wrapper

# For currency pairs displayed to 4 decimal places, one pip = 0.0001
# Yen-based currency pairs are an exception, and are displayed to only two
# decimal places (0.01)
# KNOWN_RATIO_OTHER = (1, 0.0001)
# KNOWN_RATIO_YEN = (1, 0.01)


@std_dec
def counter_pos_size(ACC_AMOUNT=1000, STOP=100, KNOWN_RATIO=0.0001,
                     RISK_PERC=0.01):
    """
    A position size calculator to use when the account currency denomination is
    the same as the counter currency (denominator) of the traded ticker.

    Parameters
    ----------
    ACCOUNT_CURR : float
        The sum value of the account from which funds will be used to place the
        trade.
    STOP : float
        The number of pips between the entry price and the stop loss exit
        price.
    KNOWN_RATIO : float
        The known unit to pip ratio for the traded ticker.
    RISK_PERC : float
        The percentage of the account in decimal format that will be risked on
        this trade.

    Returns
    ------
    float
        The trade position size in arbitary units.

    Examples
    --------
    >>> pos_size = counter_pos_size(
    ...     ACC_AMOUNT=1000, STOP=100, KNOWN_RATIO=0.0001, RISK_PERC=0.01)
    >>> print(pos_size)
    1000
    """
    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@std_dec
def base_pos_size(ACC_AMOUNT=1000, TARGET_ASK=1.0000, STOP=100,
                  KNOWN_RATIO=0.0001, RISK_PERC=0.01):
    """
    A position size calculator to use when the account currency denomination is
    the same as the base currency (nominator) of the traded ticker.

    Parameters
    ----------
    ACC_AMOUNT : float
        The sum value of the account from which funds will be used to place the
        trade.
    TARGET_ASK : float
        The asking price for the traded ticker at present.
    STOP : float
        The number of pips between the entry price and the stop loss exit
        price.
    KNOWN_RATIO : float
        The known unit to pip ratio for the traded ticker.
    RISK_PERC : float
        The percentage of the account in decimal format that will be risked on
        this trade.

    Returns
    ------
    float
        The trade position size in arbitary units.

    Examples
    --------
    >>> pos_size = base_pos_size(
    ...     ACC_AMOUNT=1000, TARGET_ASK=1.0000, STOP=100, KNOWN_RATIO=0.0001,
    ...     RISK_PERC=0.01)
    >>> print(pos_size)
    1000
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_CNT_CURR = MAX_RISK_ACC_CURR * TARGET_ASK

    VALUE_PER_PIP = MAX_RISK_CNT_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@std_dec
def counter_conv_pos_size(ACC_AMOUNT=1000.00, CONV_ASK=1.0000, STOP=100,
                          KNOWN_RATIO=0.0001, RISK_PERC=0.01):
    """
    A position size calculator to use when the account currency denomination is
    the same as the counter currency (denominator) of the conversion pair.

    The conversion pair is used to convert the risk calculated in the account
    currency, across to the target pair's counter currency.

    Parameters
    ----------
    ACC_AMOUNT : float
        The sum value of the account from which funds will be used to place the
        trade.
    CONV_ASK : float
        The asking price for the conversion ticker at present.
    STOP : float
        The number of pips between the entry price and the stop loss exit
        price.
    KNOWN_RATIO : float
        The known unit to pip ratio for the traded ticker.
    RISK_PERC : float
        The percentage of the account in decimal format that will be risked on
        this trade.

    Returns
    ------
    float
        The trade position size in arbitary units.

    Examples
    --------
    >>> pos_size = counter_conv_pos_size(
    ...     ACC_AMOUNT=1000, CONV_ASK=1.0000, STOP=100, KNOWN_RATIO=0.0001,
    ...     RISK_PERC=0.01)
    >>> print(pos_size)
    1000
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_TARGET_CNT = MAX_RISK_ACC_CURR * (1 / CONV_ASK)

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@std_dec
def base_conv_pos_size(ACC_AMOUNT=1000, CONV_ASK=1.0000, STOP=100,
                       KNOWN_RATIO=0.0001, RISK_PERC=0.01):
    """
    A position size calculator to use when the account currency denomination is
    the same as the base currency (nominator) of the conversion pair.

    The conversion pair is used to convert the risk calculated in the account
    currency, across to the target pair's counter currency.

    Parameters
    ----------
    ACC_AMOUNT : float
        The sum value of the account from which funds will be used to place the
        trade.
    CONV_ASK : float
        The asking price for the conversion ticker at present.
    STOP : float
        The number of pips between the entry price and the stop loss exit
        price.
    KNOWN_RATIO : float
        The known unit to pip ratio for the traded ticker.
    RISK_PERC : float
        The percentage of the account in decimal format that will be risked on
        this trade.

    Returns
    ------
    float
        The trade position size in arbitary units.

    Examples
    --------
    >>> pos_size = base_conv_pos_size(
    ...     ACC_AMOUNT=1000, CONV_ASK=1.000, STOP=100, KNOWN_RATIO=0.0001,
    ...     RISK_PERC=0.01)
    >>> print(pos_size)
    1000
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_TARGET_CNT = MAX_RISK_ACC_CURR * CONV_ASK

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@std_dec
def profit_loss(ENTRY=1.0, EXIT=1.1, POS_SIZE=2500, CONV_ASK=1.0, CNT=1):
    """
    Profit and loss calculator for buy trades.

    Parameters
    ----------
    ENTRY : float
        The trade's entry price.
    EXIT : float
        The trade's exit price.
    POS_SIZE : int
        The trade's position size in units.
    CONV_ASK : float
        The asking price at time of exit for the conversion pair. The
        conversion pair is defined by the account denomination against the
        traded pair counter currency.
    CNT :  {0, 1}
        Either 0 or 1, to denote whether the account denomination is either
        the base (0) or the counter (1) currency in the conversion pair.

    Returns
    -------
    float
        The trade's value in the account denomination currency.

    Examples
    --------
    >>> profit_loss_amount = profit_loss(
    ...     ENTRY=2.1443, EXIT=2.1452, POS_SIZE=1000, CONV_ASK=1.1025, CNT=1)
    >>> print(profit_loss_amount)
    0.99
    """
    PIP_DELTA = EXIT - ENTRY

    # Invert the conversion rate if the account denomination is not the counter
    # currency, i.e. the base currency, in the conversion pair, composed of the
    # traded counter currency against the account currency.
    if not int(CNT):
        CONV_ASK = (1 / CONV_ASK)

    CURR_DELTA = PIP_DELTA * CONV_ASK

    ACC_AMOUNT = CURR_DELTA * POS_SIZE

    return ACC_AMOUNT.quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_EVEN)


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
    stats["net_profit"] = results.iloc[-1]["P/L REALISED"] - 1000

    stats["win_%"] = decimal.Decimal(
        results[results["P/L AUD"] > 0]["P/L AUD"].count() /
        results["P/L AUD"].count() *
        100).quantize(decimal.Decimal("0.01"))
    stats["loss_%"] = decimal.Decimal(
        results[results["P/L AUD"] < 0]["P/L AUD"].count() /
        results["P/L AUD"].count() *
        100).quantize(decimal.Decimal("0.01"))

    stats["win_max"] = results["P/L AUD"].max()
    stats["loss_max"] = results["P/L AUD"].min()

    stats["win_mean"] = decimal.Decimal(
        results[results["P/L AUD"] > 0]["P/L AUD"].mean()
        ).quantize(decimal.Decimal("0.01"))
    stats["loss_mean"] = decimal.Decimal(
        results[results["P/L AUD"] < 0]["P/L AUD"].mean()
        ).quantize(decimal.Decimal("0.01"))

    holding_time = results["exit_datetime"] - results["entry_datetime"]
    stats["average_holding_time_per_trade"] = str(
        datetime.timedelta(seconds=holding_time.mean().seconds))

    cons_loss = 0
    list_cons_loss = []
    for row in results.iterrows():
        if row[1]["P/L AUD"] < 0:
            cons_loss += 1
            if cons_loss == 1:
                list_cons_loss.append(copy.deepcopy(cons_loss))
            else:
                list_cons_loss[-1] = copy.deepcopy(cons_loss)
        elif row[1]["P/L AUD"] >= 0:
            cons_loss = 0

    if len(list_cons_loss) > 0:
        stats["max_cons_loss"] = decimal.Decimal(max(list_cons_loss))
        stats["mean_cons_loss"] = decimal.Decimal(
            sum(list_cons_loss) / len(list_cons_loss)
            ).quantize(decimal.Decimal("1."))

    stats["trading_exp"] = (
        (stats["win_%"] / decimal.Decimal("100") * stats["win_mean"]) +
        (stats["loss_%"] / decimal.Decimal("100") * stats["loss_mean"])
        ).quantize(decimal.Decimal("0.01"))

    return stats
