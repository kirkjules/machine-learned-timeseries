import logging
import pandas as pd
from pprint import pprint
from htp.api import oanda
from htp.toolbox import dates, engine
from htp.analyse import indicator, evaluate

f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# logging.basicConfig(level=logging.INFO, format=f)
logger = logging.getLogger("htp.toolbox.engine")
logger.setLevel(level=logging.INFO)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter(f)
fh.setFormatter(fh_formatter)
logger.addHandler(fh)


def main():

    instrument = "AUD_JPY"
    queryParameters = {"granularity": "M15"}
    func = oanda.Candles.to_df
    queue_month = dates.Select(from_="2005-01-01 17:00:00",
                               to="2005-12-30 17:00:00",
                               local_tz="America/New_York"
                               ).by_month()
    date_list = []
    for i in queue_month:
        date_list.append(i)
    work = engine.ParallelWorker(date_gen=date_list,
                                 func=func,
                                 instrument=instrument,
                                 queryParameters=queryParameters)
    month = work.run()
    month_concat = pd.concat(month)
    month_clean = month_concat[~month_concat.index.duplicated()]
    month_index_dt = month_clean.set_index(
        pd.to_datetime(month_clean.index,
                       format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
    month_sorted = month_index_dt.sort_index()
    pprint(month_sorted.head())
    # Rolling average for last 4 hours
    sma_16 = indicator.smooth_moving_average(
        month_sorted, column="close", period=16)
    # Rolling average for last 24 hours
    sma_16_96 = indicator.smooth_moving_average(
        month_sorted, df2=sma_16, column="close", concat=True, period=96)
    print(sma_16_96.head(20))
    entry_exit = evaluate.buy_signal_cross(
        sma_16_96, "close_sma_16", "close_sma_96")
    print(entry_exit.head(10))


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

# Preparation:
# ------------
# 1. Set the data paramaters.
#     a) ticker
#     b) date range: generate with dates module
#     c) granularity

# 2. Call the data via either single, threading or multiprocessing functions.
#     - The processing functions wrap the oanda.Candles api function.

# 3. Clean and process the data for analysis.

# Analysis - phase one:
# ---------------------
# 1. Compute indicator(s) on timeseries

# 2. Generate entry and exit signals from indicator(s) with standard rules.

# 3. Query entry and exit prices for signals.

# 4. Calculate position size and profit/loss for trades.

# 5. Generate trade system report from analysis table.
#     - Columns: Entry Timestamp, Entry Price, Exit Timestamp, Exit Price,
#       Position Size, Profit/Loss Pips, Profit/Loss AUD, Realized Profit/Loss
#       AUD

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
