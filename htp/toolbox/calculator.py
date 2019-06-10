"""Position Sizing"""

import decimal
import functools


def standardise_decimal(func):

    @functools.wraps(func)
    def wrapper(**kwargs):

        decimal_kwargs = {}
        for kwarg in kwargs:
            decimal_kwargs[kwarg] = decimal.Decimal(kwargs[kwarg])

        return func(**decimal_kwargs).quantize(
            decimal.Decimal("1."), rounding=decimal.ROUND_DOWN)

    return wrapper
# For currency pairs displayed to 4 decimal places, one pip = 0.0001
# Yen-based currency pairs are an exception, and are displayed to only two
# decimal places (0.01)
# KNOWN_RATIO_OTHER = (1, 0.0001)
# KNOWN_RATIO_YEN = (1, 0.01)


"""
If account denomination is the same as the counter currency (denominator)
"""


@standardise_decimal
def counter_pos_size(ACCOUNT_CURR=1000, STOP=100, KNOWN_RATIO=0.0001,
                     RISK_PERC=0.01):

    MAX_RISK_COUNTER_CURR = ACCOUNT_CURR * RISK_PERC

    VALUE_PER_PIP = MAX_RISK_COUNTER_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE

# ACCOUNT_USD = 5000
# Where the STOP is in pips.
# TRADE = {"ticker": "EUR_USD", "STOP": 200}

# Where 1% of the account is the maximum amount risked per trade.
# Multiply the account balance and maximum percentage amount to be risked to
# give the dollar amount risked, e.g.
# USD 5000 * 1% = USD 50
# MAX_RISK_USD = ACCOUNT_USD * 0.01

# Divide the amount risked by the trade stop amount in pips, e.g.
# (USD 50) / (200 pips) = USD 0.25 / pip
# VALUE_PER_PIP = MAX_RISK_USD / TRADE["STOP"]

# Multiply the value per pip by a known unit/pip value ratio of EUR/USD, e.g.
# 10K units equates to 1 pip per 1 USD to give,
# USD 0.25 per pip * [(10K units of EUR/USD) / (USD 1 per pip)] = 2500 units
# of EUR/USD.
# POSITION_SIZE = VALUE_PER_PIP * (10000 / 1)


"""
If the account denomination is the same as the base currency (nominator).
"""


@standardise_decimal
def base_pos_size(ACCOUNT_CURR=1000, TARGET_ASK=1.0000, STOP=100,
                  KNOWN_RATIO=0.0001, RISK_PERC=0.01):

    MAX_RISK_ACC_CURR = ACCOUNT_CURR * RISK_PERC

    MAX_RISK_COUNTER_CURR = TARGET_ASK * MAX_RISK_ACC_CURR

    VALUE_PER_PIP = MAX_RISK_COUNTER_CURR / STOP

    POSITION_SIZE = VALUE_PER_PIP * (1 / KNOWN_RATIO)

    return POSITION_SIZE

# ACCOUNT_EUR = 5000
# TRADE = {"ticker": "EUR_USD", "STOP": 200}

# Where 1% of the account is the maximum amount risked per trade, e.g.
# EUR 5000 * 1% = EUR 50
# MAX_RISK_EUR = ACCOUNT_EUR * 0.01

# Convert to USD because the currency pair's value is calculated by the counter
# currency. To do this:
    # 1. Find the current exchange rate for EUR/USD:
    # 1 EUR is $1.5000 (EUR/USD = 1.5000)
    # 2. To find the value in USD, multiply the current exchange rate for
    # EUR/USD by the amount of euros being risked:
    # (EUR/USD 1.5000) * EUR 50 = approx USD 75.00
# MAX_RISK_USD = BID * MAX_RISK_EUR

# Divide risk in USD by stop loss in pips, e.g.
# (USD 75.00) / (200 pips) = USD 0.375 / pip
# VALUE_PER_PIP = MAX_RISK_USD / TRADE["STOP"]

# Multiply the value per pip move by the known unit-to-pip value ratio, e.g.
# (USD 0.375 per pip) * [(10K units of EUR/USD) / (USD 1 per pip)] = 3750 units
# of EUR/USD
# POSITION_SIZE = VALUE_PER_PIP * (10000 / 1)


"""
If the account denomination is not in the currency pair trade, but the same
as the conversion pair's counter currency.
"""


@standardise_decimal
def counter_conv_pos_size(ACCOUNT_CURR=1000.00, TARGET_CNT_ACC_CURR_ASK=1.0000,
                          STOP=100, KNOWN_RATIO=0.0001, RISK_PERC=0.01):

    MAX_RISK_ACC_CURR = ACCOUNT_CURR * RISK_PERC

    MAX_RISK_TARGET_CNT = (1 / TARGET_CNT_ACC_CURR_ASK) * MAX_RISK_ACC_CURR

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * KNOWN_RATIO

    return POSITION_SIZE

# Remember, the value of a currency pair is in the counter currency.

# ACCOUNT_USD = 5000
# TRADE = {"ticker": "EUR_GBP", "STOP": 200}

# Where 1% of the account is the maximum amount risked per trade, e.g.
# USD 5000 * 1% = USD 50
# MAX_RISK_USD = ACCOUNT_USD * 0.01

# Convert the USD risk to GBP risk via:
    # 1. Find the current exchange rate for GBP/USD:
    # 1 GBP is $1.7500 (GBP/USD = 1.7500)
    # 2. To find the value in USD, multiply the inverse of the current exchange
    # rate for GBP/USD by the amount of USD being risked:
    # (1 / (GBP/USD 1.7500)) * USD 50 = GBP 28.57
# MAX_RISK_GBP = (1 / BID) * MAX_RISK_USD

# Convert GBP risk amount to pips by dividing the stop loss by pips, e.g.
# (GBP 28.57) / (200 pips) = GBP 0.14 / pip
# VALUE_PER_PIP = MAX_RISK_GBP / TRADE["STOP"]

# Multiply the value-per-pip by the known unit-to-pip value ratio, e.g.
# (GBP 0.14 per pip) * [(10K units of EUR/GBP) / (GBP 1 per pip)] = approx 1429
# EUR/GBP
# POSITION_SIZE = VALUE_PER_PIP * (10000 / 1)


"""
If the account denomination is not in the currency pair traded, but the same as
the conversion pair's base currency.
"""


@standardise_decimal
def base_conv_pos_size(ACCOUNT_CURR=1000, TARGET_CNT_ACC_CURR_ASK=1.0000,
                       STOP=100, KNOWN_RATIO=0.0001, RISK_PERC=0.01):

    MAX_RISK_ACC_CURR = ACCOUNT_CURR * RISK_PERC

    MAX_RISK_TARGET_CNT = TARGET_CNT_ACC_CURR_ASK * MAX_RISK_ACC_CURR

    VALUE_PER_PIP = MAX_RISK_TARGET_CNT / STOP

    POSITION_SIZE = VALUE_PER_PIP * KNOWN_RATIO

    return POSITION_SIZE


# ACCOUNT_CHF = 5000
# TRADE = {"ticker": "USD_JPY", "STOP": 100}

# Where  1% of the account is the maximum amount risked per trade, e.g.
# CHF 5000 * 1% = CHF 50
# MAX_RISK_CHF = ACCOUNT_CHF * 0.01

# Convert the value of the account currency (CHF) to the ticker's counter
# currency (denominator).
# Since the account is in the same denomination as the conversion pair's base
# currency (CHF/JPY), simply multiply the amount risked by the exchange rat e.g
# CHF 50 * (JPY 85.00/CHF 1) = JPY 4250
# MAX_RISK_JPY = BID * MAX_RISK_CHF

# Divide the max risk by the stop loss in pips, e.g.
# (JPY 4250) / (100 pips) = JPY 42.50 / pip
# VALUE_PER_PIP = MAX_RISK_JPY / TRADE["STOP"]

# Multiply by a known unit-to-pip value ratio, e.g.
# (JPY 42.50 per pip) * [(100 units of USD/JPY) / (JPY 1 per pip)] = approx
# 4250 USD/JPY
# POSITION_SIZE = VALUE_PER_PIP * (100 / 1)
