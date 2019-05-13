import logging
from api import oanda

logging.basicConfig(level=logging.INFO)

cf = "config.ini"
live = False
ticker = ""
arguments = {"from": "", "to": "", "granularity": ""}
data = oanda.Candles(cf, ticker, arguments, live)
if data.status != 200:
    pass

# ["AUD_CAD", "NZD_USD", "NZD_JPY", "AUD_JPY", "AUD_NZD",
# "AUD_USD", "USD_JPY", "USD_CHF", "GBP_CHF", "NZD_CAD", "CAD_JPY",
# "USD_CAD", "EUR_GBP", "EUR_CHF", "EUR_JPY", "GBP_JPY", "GBP_USD",
# "EUR_USD", "EUR_NZD", "GBP_CAD", "EUR_CAD", "CHF_JPY", "GBP_AUD",
# "EUR_AUD", "GBP_NZD"]:
# "USB10Y_USD", "UK10YB_GBP", "AU200_AUD", "BCO_USD",
# "DE10YB_EUR", "XCU_USD", "CORN_USD", "EU50_EUR", "FR40_EUR",
# "DE30_EUR", "XAU_AUD", "HK33_HKD", "IN50_USD", "JP225_USD",
# "NATGAS_USD", "XAG_AUD", "SOYBN_USD", "SUGAR_USD", "SPX500_USD",
# "NAS100_USD", "WTICO_USD", "WHEAT_USD"]:

# Read in the ticker data
    # :ticker
    # :date range
    #    :generate with dates module
    # :granularity
    # :call data via either single, threading or multiprocessing functions.
    #    :functions wrap the oanda.Candle api function.

# Apply indicator(s) to timeseries
    # :indicator(s)

# Apply model to dataset
    # :stop loss
    # :entry
    # :take profit
    # :record result

# Analyse results with decision trees
    # :scikit-learn
    # :parameteres

# Edit model and reapply

# Analyse results

# Test model forward 1 corresponding unit
    # {M15: 1FYQ,
    #   H1: 1FY,
    #   H4: 4FY,
    #    D: 2FY}

# Repeat and log everything.
