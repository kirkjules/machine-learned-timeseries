import logging
from pprint import pprint
from htp.api import oanda
from htp.toolbox import dates, engine

f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# logging.basicConfig(level=logging.INFO, format=f)
logger = logging.getLogger("htp.toolbox.engine")
logger.setLevel(level=logging.INFO)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter(f)
fh.setFormatter(fh_formatter)
logger.addHandler(fh)


def main():

    configFile = "./config.ini"
    instrument = "AUD_JPY"
    queryParameters = {"granularity": "D"}
    live = False
    func = oanda.Candles
    date_list = []
    for i in dates.Select().by_month(period=5):
        date_list.append(i)

    data = engine.ParallelWorker(date_gen=date_list,
                                 func=func,
                                 configFile=configFile,
                                 instrument=instrument,
                                 queryParameters=queryParameters,
                                 live=live).run()

    pprint(data)


if __name__ == "__main__":
    main()

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
#    :functions wrap the oanda.Candles api function.

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
