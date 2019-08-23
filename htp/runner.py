import sys
import copy
import pandas as pd
from loguru import logger
from decimal import Decimal
from pprint import pprint
from htp.api import oanda
from htp.toolbox import dates, calculator, workshop
from htp.analyse import indicator, evaluate, predict

logger.enable("htp.api.oanda")


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

    Examples
    --------
    >>> func = oanda.Candles.to_df
    >>> instrument = "AUD_JPY"
    >>> queryParameters = {
    ...    "from": "2012-01-01 17:00:00", "to": "2012-06-27 17:00:00",
    ...    "granularity": "H1", "price": "M"}
    >>> data_mid = setup(
    ...    func=func, instrument=instrument, queryParameters=queryParameters)
    >>> data_mid.head()
                           open    high     low   close
    2012-01-01 22:00:00  78.667  78.892  78.627  78.830
    2012-01-01 23:00:00  78.824  78.879  78.751  78.768
    2012-01-02 00:00:00  78.776  78.839  78.746  78.803
    2012-01-02 01:00:00  78.807  78.865  78.746  78.790
    2012-01-02 02:00:00  78.787  78.799  78.703  78.733
    """

    queryParameters_copy = copy.deepcopy(queryParameters)
    date_gen = dates.Select(
        from_=queryParameters_copy["from"], to=queryParameters_copy["to"],
        local_tz="America/New_York").by_month()
    date_list = []
    for i in date_gen:
        queryParameters_copy["from"] = i["from"]
        queryParameters_copy["to"] = i["to"]
        date_list.append(copy.deepcopy(queryParameters_copy))
    data_query = workshop.ParallelWorker(
        func, "queryParameters", iterable=date_list, instrument=instrument
        ).prl()
    data_concat = pd.concat(data_query)
    data_clean = data_concat[~data_concat.index.duplicated()]
    data = data_clean.sort_index()
    data.name = "{}".format(queryParameters_copy["price"])
    return data.astype("float")


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

    Examples
    --------
    >>> from htp.api.oanda import Candles
    >>> from htp.analyse import indicator, evaluate
    >>> data_mid = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> data_bid = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1", "price": "B",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> data_ask = Candles.to_df(
    ...     instrument="AUD_JPY",
    ...     queryParameters={"granularity": "H1", "price": "A",
    ...                      "from": "2018-06-11T16:00:00.000000000Z",
    ...                      "count": 2000})
    >>> sma_5 = indicator.smooth_moving_average(
    ...     data_mid, column="close", period=5)
    >>> sma_5_10 = indicator.smooth_moving_average(
    ...     data_mid, column="close", df2=sma_5, concat=True, period=10)
    >>> signal(data_price_in=data_ask, data_price_out=data_bid,
    ...     sig_frame=sma_5_10, system=("close_sma_5", "close_sma_10")).head(5)
                    entry                exit entry_A  exit_B
    0 2018-06-12 02:00:00 2018-06-12 10:00:00  83.987  83.833
    1 2018-06-13 03:00:00 2018-06-13 20:00:00  83.671  83.545
    2 2018-06-14 15:00:00 2018-06-14 17:00:00  83.149  82.869
    3 2018-06-15 06:00:00 2018-06-15 11:00:00  82.780  82.632
    4 2018-06-18 08:00:00 2018-06-18 14:00:00  82.158  82.124
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
    label = "{0}_{1}".format(i[0], i[1])
    entry_exit_sort = signal(
        data_price_in=data_price_in, data_price_out=data_price_out,
        sig_frame=sig_frame, system=i)
    d_results = count(entry_exit_sort)
    # Note comparing all systems by first 500 signals.
    kpi = pd.DataFrame.from_dict(
        {label: calculator.performance_stats(
            d_results[:500].copy())}, orient="index")
    print("\nSystem: {0} {1}\n".format(i[0], i[1]))
    print("\n{}\n".format(kpi))
    return (kpi, label, d_results, entry_exit_sort)


def main():

    # DATA --> object: data_temp
    pd.set_option("display.max_columns", 12)
    pd.set_option("display.max_rows", 500)
    func = oanda.Candles.to_df
    instrument = "AUD_JPY"
    queryParameters = {
        "from": "2012-01-01 17:00:00", "to": "2012-06-27 17:00:00",
        "granularity": "H1", "price": "M"}

    data_mid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    queryParameters["price"] = "A"
    data_ask = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)
    queryParameters["price"] = "B"
    data_bid = setup(
        func=func, instrument=instrument, queryParameters=queryParameters)

    sys.exit()
    # PROPERTIES --> object: data_temp
    print("Ichimoku Kinko Hyo")
    iky = indicator.ichimoku_kinko_hyo(data_mid)
    iky_close = pd.concat([iky, data_mid["close"]], axis=1)
    iky_close["iky_cat"] = iky_close.apply(evaluate.iky_cat, axis=1)

    print("Relative Strength Index")
    rsi = indicator.relative_strength_index(data_mid)

    print("Stochastic")
    stoch = indicator.stochastic(data_mid)
    stoch["stoch_diff"] = stoch["%K"] - stoch["%D"]

    print("Moving Average Convergence Divergence")
    macd = indicator.moving_average_convergence_divergence(data_mid)

    print("Average Directional Movement")
    adx = indicator.Momentum.average_directional_movement(data_mid)

    print("Average True Range")
    atr = indicator.Momentum.average_true_range(data_mid)

    print("Difference Change")
    data_mid["close_diff"] = data_mid["close"] - data_mid["close"].shift(1)
    data_atr = pd.concat([data_mid, atr["ATR"]], axis=1)
    data_atr["diff_atr"] = data_atr["close_diff"] / data_atr["ATR"]
    data_atr = data_atr.round(4)

    print("Concatenate Prep")
    data_temp = pd.concat([data_mid, iky_close["iky_cat"], rsi["RSI"],
                           stoch[["%K", "%D", "stoch_diff"]], adx["ADX"],
                           macd[["MACD", "Signal", "Histogram"]],
                           data_atr[["diff_atr", "ATR"]]], axis=1)

    # SYSTEMS
    # periods = [80, 96, 100]
    periods = [5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 45, 48, 50, 56, 64, 70, 72, 80, 90, 96, 100]

    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(
            data_temp, column="close", period=i)
        avgs.append(avg)
    sma_x_y = pd.concat(avgs, axis=1)

    # EXTRA PROPERTIES (DERIVED FROM SYSTEM) --> object: data_sma_diff
    print("Difference from Simple Moving Average curves")
    data_sma_diff = pd.concat([data_temp[["close", "ATR"]], sma_x_y], axis=1)
    for i in periods:
        data_sma_diff["close_sma_{}_diff".format(i)] = \
            data_sma_diff["close"] - \
            data_sma_diff["close_sma_{}".format(i)]
        data_sma_diff.drop("close_sma_{}".format(i), axis=1, inplace=True)
        data_sma_diff["close_sma_{}_diff_atr".format(i)] = \
            data_sma_diff["close_sma_{}_diff".format(i)] / \
            data_sma_diff["ATR"]

    # data_temp_final = pd.concat(
    #     [data_temp, data_sma_diff.drop(["close", "ATR"], axis=1)], axis=1)

    # print(data_temp_final.columns)

    s = [("close_sma_{}".format(i), "close_sma_{}".format(j))
         for i in periods for j in periods if i < j]

    # SIGNALS (OUTPUT FROM SYSTEM) --> object: results
    # RESULTS (CALCULATED FROM SIGNALS) --> objects: stats_results (aggregate),
    # results (by system)
    results = workshop.ParallelWorker(
        assess, "i", data_ask, data_bid, sma_x_y, iterable=s).prl()

    r_frames = []
    r_results = {}
    for i in results:
        r_frames.append(i[0])
        r_results[i[1]] = (i[2], i[3])  # [:550]

    results_frame = pd.concat(r_frames, axis=0)
    print("\n{}\n".format(results_frame))
    results_frame.to_csv("stats_out.csv")
    return data_temp, data_sma_diff.round(4), results_frame, r_results


if __name__ == "__main__":
    data_ind, data_sma_diff, stats_results, results = main()

    stats_results_filter = stats_results[stats_results["win_%"] >= 40.0].copy()
    print(stats_results_filter.index)
    res_rf = []
    for i in stats_results_filter.index:
        print("\nSystem: {}\n".format(i))
        res_data = results[i][0]
        entry_data = results[i][1]

        data_ind_sma = pd.concat(
            [data_ind,
             data_sma_diff[
                 ["close_sma_{}_diff".format(i.split("_")[2]),
                  "close_sma_{}_diff_atr".format(i.split("_")[2]),
                  "close_sma_{}_diff".format(i.split("_")[5]),
                  "close_sma_{}_diff_atr".format(i.split("_")[5])]
             ]], axis=1)

        print(data_ind_sma.columns)

        comp_win, base_line = predict.random_forest(
            data_ind_sma, res_data.copy())

        res_base = base_line.merge(entry_data, how="left", left_index=True,
                                   right_on="entry", validate="1:1")
        res_base_count = count(res_base)
        print("\n# trades base line: {}\n".format(len(res_base_count)))
        res_base_perf = calculator.performance_stats(res_base_count)

        res_pred = comp_win.merge(entry_data, how="left", left_index=True,
                                  right_on="entry", validate="1:1")
        res_pred_count = count(res_pred)
        print("\n# trades predicted: {}\n".format(len(res_pred_count)))
        res_pred_perf = calculator.performance_stats(res_pred_count)

        kpi = pd.DataFrame.from_dict(
            {"base_{0}_{1}".format(
                i.split("_")[2], i.split("_")[5]): res_base_perf,
             "prediction_{0}_{1}".format(
                i.split("_")[2], i.split("_")[5]): res_pred_perf},
            orient="index")

        pprint(kpi)
        res_rf.append(kpi)

    df_res_rf = pd.concat(res_rf, axis=0)
    df_res_rf.to_csv("rf_stats_out.csv")

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
