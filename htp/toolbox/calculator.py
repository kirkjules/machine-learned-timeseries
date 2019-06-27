"""Module for calculating position sizes."""

import decimal
import functools


def standardise_decimal(func):
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


@standardise_decimal
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
    >>> from htp.toolbox import calculator
    >>> pos_size = calculator.counter_pos_size(ACC_AMOUNT=1000, STOP=100,
                                               KNOWN_RATIO=0.0001,
                                               RISK_PERC=0.01)
    >>> print(pos_size)
    """
    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    VALUE_PER_PIP = MAX_RISK_ACC_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@standardise_decimal
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
    >>> from htp.toolbox import calculator
    >>> pos_size = calculator.base_pos_size(ACC_AMOUNT=1000,
                                            TARGET_ASK=1.0000, STOP=100,
                                            KNOWN_RATIO=0.0001, RISK_PERC=0.01)
    >>> print(pos_size)
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_CNT_CURR = MAX_RISK_ACC_CURR * TARGET_ASK

    VALUE_PER_PIP = MAX_RISK_CNT_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@standardise_decimal
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
    >>> from htp.toolbox import calculator
    >>> pos_size = calculator.counter_conv_pos_size(
                     ACC_AMOUNT=1000, CONV_ASK=1.0000,
                     STOP=100, KNOWN_RATIO=0.0001, RISK_PERC=0.01)
    >>> print(pos_size)
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_TARGET_CNT = MAX_RISK_ACC_CURR * (1 / CONV_ASK)

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@standardise_decimal
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
    >>> from htp.toolbox import calculator
    >>> pos_size = calculator.base_conv_pos_size(
                     ACC_AMOUNT=1000, CON_ASK=1.000,
                     STOP=100, KNOWN_RATIO=0.0001, RISK_PERC=0.01)
    >>> print(pos_size)
    """

    MAX_RISK_ACC_CURR = ACC_AMOUNT * RISK_PERC

    MAX_RISK_TARGET_CNT = MAX_RISK_ACC_CURR * CONV_ASK

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE.quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_UP)


@standardise_decimal
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
    >>> from htp.toolbox import calculator
    >>> profit_loss_amount = calculator.profit_loss(ENTRY=2.1443,
                                                    EXIT=2.1452,
                                                    POS_SIZE=1000,
                                                    CONV_ASK=1.1025,
                                                    CNT=1)
    >>> print(profit_loss_amount)
    0.99225
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
            decimal.Decimal("0.00001"), rounding=decimal.ROUND_HALF_EVEN)
