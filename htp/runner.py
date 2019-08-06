import copy
import logging
import pandas as pd
from decimal import Decimal
from htp.api import oanda
from htp.toolbox import dates, engine, calculator, workshop
from htp.analyse import indicator, evaluate

f = "%(asctime)s - %(name)s - %(message)s"
# logging.basicConfig(level=logging.INFO, format=f)
logger = logging.getLogger("htp.toolbox.engine")
logger.setLevel(level=logging.INFO)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter(f)
fh.setFormatter(fh_formatter)
logger.addHandler(fh)


def setup(func, instrument, queryParameters):
    """
    Wrapper function that groups arguments parsing, data querying and data
    clean up.

    Parameters
    ----------
    func : {"oanda.Candles.to_json", "oanda.Candles.to_df"}
        The function that should be used to query the ticker data.

    instrument : str
        The ticker instrument whose timeseries should be queried.

    queryParameters : dict
        Variables that will be parsed in the request body onto the api
        endpoint.

    Returns
    -------
    pandas.core.frame.DataFrame
        The timeseries ticker data stored in a pandas DataFrame and sorted by
        datetime index.

    Notes
    -----
    Flow
    1. State date/time range with datetime strings listed in ISO-8601 format.
    2. Convert date/time to UTC.
    Note: Parse to query in RFC3339 format: "YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ"
    3. State granularity
    Note: daily candles should keep default setting for dailyAlignment and
            alignmentTimezone settings. Smooth must be set to True to ensure
            same values as displayed by Oanda on the online portal.
    4. Query data.
    Note: any actions logged will be in UTC time. If the user needs a timestamp
            displayed in local time this functionality will be applied in the
            relevant functions and methods.
    """

    queryParameters_copy = copy.deepcopy(queryParameters)
    queue_dates = dates.Select(
        from_=queryParameters_copy["from"], to=queryParameters_copy["to"],
        local_tz="America/New_York").by_month()
    date_list = []
    for i in queue_dates:
        date_list.append(i)
    work = engine.ParallelWorker(date_gen=date_list,
                                 func=func,
                                 instrument=instrument,
                                 queryParameters=queryParameters_copy)
    data_query = work.run()
    data_concat = pd.concat(data_query)
    data_clean = data_concat[~data_concat.index.duplicated()]
    data = data_clean.sort_index()
    data.name = "{}".format(queryParameters_copy["price"])
    return data


def signal(data_price_in, data_price_out, sig_frame, system):
    """
    Append price data to entry and exit timestamps generated from signals
    crossing.

    Parameters
    ----------
    data_price_in : pandas.core.frame.DataFrame
        The dataframe that contains the real entry price, i.e. the ask or bid

    data_price_out : pandas.core.frame.DataFrame
        The dataframe that contains the real exit price, i.e. the ask or bid

    sig_frame : pandas.core.frame.DataFrame
        The dataframe containing the signals to be assessed against each other
        to provide entry and exit timestamps.

    system : tuple
        The signals that should be assessed against each other.

    Returns
    -------
    pandas.core.frame_DataFrame
        A pandas dataframe with the action price appended in an appropriately
        labelled column, matching the format: {sig_col}_{price}.

    Notes
    -----
    For a buy trade, the ask price is used for entry and the bid price is used
    for exit.
    For a sell trade, the bid price is used for entry and the ask price is used
    for exit.
    """
    entry_exit = evaluate.signal_cross(sig_frame, system[0], system[1])

    entry_exit_in = entry_exit.merge(
        data_price_in["open"].to_frame(), how="left", left_on="entry",
        right_index=True, validate="1:1").rename(
            columns={"open": "entry_A"})

    entry_exit_in_out = entry_exit_in.merge(
        data_price_out["open"].to_frame(), how="left", left_on="exit",
        right_index=True, validate="1:1").rename(
            columns={"open": "exit_B"})

    entry_exit_sort = entry_exit_in_out.sort_values(
        by=["entry"]).reset_index(drop=True)

    return entry_exit_sort


def count(trades):
    """
    Function to calculate trade information: P/L Pips, P/L AUD, Position Size,
    Realised P/L.

    Parameters
    ----------
    trades : pandas.core.frame.DataFrame
        A pandas dataframe that contains entry and exit prices in respective
        columns, with each row representing a individual trade.

    Returns
    -------
    pandas.core.frame.DataFrame
        The original parsed dataframe with appended columns contain the
        calculated information respective to each trade.
    """
    AMOUNT = 1000
    STOP = 50
    KNOWN_RATIO = 0.01
    RISK_PERC = 0.01
    trades["P/L PIPS"] = trades.apply(
        lambda x: (
            (Decimal(x["exit_B"]) - Decimal(x["entry_A"]))
            * Decimal("100")).quantize(Decimal(".1")), axis=1)
    d_pos_size = {}
    for i in trades.iterrows():
        trade = i[1]
        size = calculator.base_conv_pos_size(
            ACC_AMOUNT=AMOUNT, CONV_ASK=trade["entry_A"], STOP=STOP,
            KNOWN_RATIO=KNOWN_RATIO, RISK_PERC=RISK_PERC)
        profit = calculator.profit_loss(
            ENTRY=trade["entry_A"], EXIT=trade["exit_B"], POS_SIZE=size,
            CONV_ASK=trade["entry_A"], CNT=0)
        AMOUNT += profit
        d_pos_size[trade["entry"]] = {"POS_SIZE": size, "P/L AUD": profit,
                                      "P/L REALISED": AMOUNT}
    counting = pd.DataFrame.from_dict(d_pos_size, orient="index")
    entry_exit_complete = trades.merge(
        counting, how="left", left_on="entry", right_index=True,
        validate="1:1")

    return entry_exit_complete


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def assess(data_price_in, data_price_out, sig_frame, i=None):
    # s_results = []
    # for i in iter(iterable):
    entry_exit_sort = signal(
        data_price_in=data_price_in, data_price_out=data_price_out,
        sig_frame=sig_frame, system=i)
    d_results = count(entry_exit_sort)
    kpi = pd.DataFrame.from_dict(
        {"{0}_{1}".format(i[0], i[1]):
         calculator.performance_stats(d_results)}, orient="index")
    # lock.acquire()
    print("\nSystem: {0} {1}\n".format(i[0], i[1]))
    print(d_results.tail())
    print("\n{}".format(kpi))
    # lock.release()
    # s_results.append(kpi)
    return kpi  # s_results


def main():

    pd.set_option("display.max_columns", 12)
    pd.set_option("display.max_rows", 500)
    func = oanda.Candles.to_df
    instrument = "AUD_JPY"
    queryParameters = {
        "from": "2019-01-01 17:00:00", "to": "2019-06-27 17:00:00",
        "granularity": "M15", "price": "M"}

    data_mid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    queryParameters["price"] = "A"
    data_ask = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    queryParameters["price"] = "B"
    data_bid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)

    periods = [5, 6, 7]
    # , 8, 9, 10, 12, 14, 15, 16, 18, 20, 24, 25, 28, 30, 32,
    # 35, 36, 40, 45, 48, 50, 56, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(
            data_mid, column="close", period=i)
        avgs.append(avg)
    sma_x_y = pd.concat(avgs, axis=1)

    s = [("close_sma_{}".format(i), "close_sma_{}".format(j))
         for i in periods for j in periods if i < j]

    results = workshop.ParallelWorker(
        assess, "i", data_ask, data_bid, sma_x_y, iterable=s).prl()

    results_frame = pd.concat(results, axis=0)
    print("\n{}".format(results_frame))
    # results_frame.to_csv("stats_out.csv")
    return data_mid, sma_x_y, results_frame


if __name__ == "__main__":
    data_mid, sma_x_y, stats_results = main()

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

# Indicator and ML prep:
# ----------------------
# 1. Complete indicator suite.
#    a) Base calculations on Investopedia and record the math in functions'
# docstrings.
#    b) Note/study the primary strategies for each respective indicator.
# 2. Download and employ open source libraries TA-Lib and Tulip Indicators to
# generate equivalent results on same datasets established in indicator.py
# docstrings.
# 3. Design a framework to test indicator.py against open source standard as
# well as manually compare against TradingView and Oanda results/documentation.
#    a) Employ pytest to define modules, classes and functions the will
# comprise the framework.
#    b) Record the statistical variations between different indicator methods.
#    c) Conclude the appropriate next steps required to ensure that subsequent
# ML analysis isn't compromised.

# Machine Learning: Random Forest Classifer
# -----------------------------------------
# 1. Work through tutorial(s).
# 2. Write script for ML process with n features.
# 3. Apply script to indicator suite as is. Evaluate results.
# 4. Enhance the feature suite to include relative indicator i.e. distance
# between price and signal, indicator from different time frame, etc. Evaluate
# result.

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
