import logging
import pandas as pd
from pprint import pprint
from decimal import Decimal
from htp.api import oanda
from htp.toolbox import dates, engine, calculator
from htp.analyse import indicator, evaluate

f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# logging.basicConfig(level=logging.INFO, format=f)
logger = logging.getLogger("htp.toolbox.engine")
logger.setLevel(level=logging.INFO)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter(f)
fh.setFormatter(fh_formatter)
logger.addHandler(fh)


def setup(instrument, queryParameters, from_, to):

    func = oanda.Candles.to_df
    queue_month = dates.Select(
        from_=from_, to=to, local_tz="America/New_York").by_month()
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
    return month_clean.sort_index()


def sig_data(instrument, queryParameters, price, from_, to, sig, sig_frame):

    queryParameters["price"] = price
    sig_clean_price = setup(
        instrument=instrument, queryParameters=queryParameters, from_=from_,
        to=to)
    entry_exit_price = sig_frame.merge(
        sig_clean_price["open"].to_frame(), how="left", left_on=sig,
        right_index=True, validate="1:1").rename(
            columns={"open": "{0}_{1}".format(sig, price)})
    return entry_exit_price


def main():

    instrument = "AUD_JPY"
    queryParameters = {"granularity": "M15"}
    from_ = "2019-01-01 17:00:00"
    to = "2019-06-27 17:00:00"
    month_clean = setup(instrument=instrument, queryParameters=queryParameters,
                        from_=from_, to=to)
    pprint(month_clean.head())
    # Rolling average for last 4 hours
    sma_16 = indicator.smooth_moving_average(
        month_clean, column="close", period=16)
    print(sma_16.tail())
    # Rolling average for last 24 hours
    sma_16_96 = indicator.smooth_moving_average(
        month_clean, df2=sma_16, column="close", concat=True, period=96)
    print(sma_16_96.tail())
    entry_exit = evaluate.signal_cross(
        sma_16_96, "close_sma_16", "close_sma_96")
    print(entry_exit.head())
    entry_exit_ask = sig_data(
        instrument=instrument, queryParameters=queryParameters, from_=from_,
        to=to, price="A", sig="entry", sig_frame=entry_exit)
    print(entry_exit_ask.head())
    entry_exit_ask_bid = sig_data(
        instrument=instrument, queryParameters=queryParameters, from_=from_,
        to=to, price="B", sig="exit", sig_frame=entry_exit_ask)
    entry_exit_sort = entry_exit_ask_bid.sort_values(
        by=["entry"]).reset_index(drop=True)
    print(entry_exit_sort.head())
    entry_exit_sort["P/L PIPS"] = entry_exit_sort.apply(
        lambda x: (
            (Decimal(x["exit_B"]) - Decimal(x["entry_A"]))
            * Decimal("100")).quantize(Decimal(".1")), axis=1)
    AMOUNT = 1000
    STOP = 50
    KNOWN_RATIO = 0.01
    RISK_PERC = 0.01
    d_pos_size = {}
    for i in entry_exit_sort.iterrows():
        tr = i[1]
        size = calculator.base_conv_pos_size(
            ACC_AMOUNT=AMOUNT, CONV_ASK=tr["entry_A"], STOP=STOP,
            KNOWN_RATIO=KNOWN_RATIO, RISK_PERC=RISK_PERC)
        profit = calculator.profit_loss(
            ENTRY=tr["entry_A"], EXIT=tr["exit_B"], POS_SIZE=size,
            CONV_ASK=tr["entry_A"], CNT=0)
        AMOUNT += profit
        d_pos_size[tr["entry"]] = {"POS_SIZE": size, "P/L AUD": profit,
                                   "P/L REALISED": AMOUNT}
    counting = pd.DataFrame.from_dict(d_pos_size, orient="index")
    entry_exit_complete = entry_exit_sort.merge(
        counting, how="left", left_on="entry", right_index=True,
        validate="1:1")

    return month_clean, sma_16_96, entry_exit_complete


if __name__ == "__main__":
    month_clean, sma_16_96, entry_exit = main()

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
