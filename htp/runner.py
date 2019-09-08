import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from loguru import logger
from decimal import Decimal
from pprint import pprint
from htp.toolbox import calculator, workshop
from htp.analyse import evaluate, machine_learn


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
            (Decimal(x["exit_price"]) - Decimal(x["entry_price"]))
            * Decimal("100")).quantize(Decimal(".1")), axis=1)
    d_pos_size = {}
    # for i in trades.iterrows():
    for trade in trades.itertuples():
        # trade = i[1]
        size = calculator.base_conv_pos_size(
            ACC_AMOUNT=AMOUNT, CONV_ASK=trade[2], STOP=STOP,
            KNOWN_RATIO=KNOWN_RATIO, RISK_PERC=RISK_PERC)
        profit = calculator.profit_loss(
            ENTRY=trade[2], EXIT=trade[4],
            POS_SIZE=size, CONV_ASK=trade[4], CNT=0)
        AMOUNT += profit
        d_pos_size[trade[1]] = {
            "POS_SIZE": size, "P/L AUD": profit, "P/L REALISED": AMOUNT}
    counting = pd.DataFrame.from_dict(d_pos_size, orient="index")
    entry_exit_complete = trades.merge(
        counting, how="left", left_on="entry_datetime", right_index=True,
        validate="1:1")

    return entry_exit_complete


def count_unrealised(data_mid, trades):
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
    RISK_PERC = 0.0025
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
                size = calculator.base_conv_pos_size(
                    ACC_AMOUNT=AMOUNT, CONV_ASK=trade["entry_price"],
                    STOP=STOP, KNOWN_RATIO=KNOWN_RATIO, RISK_PERC=RISK_PERC)
                profit = calculator.profit_loss(
                    ENTRY=trade["entry_price"], EXIT=trade["exit_price"],
                    POS_SIZE=size, CONV_ASK=trade["entry_price"], CNT=0)
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


def gen_signals(data_mid, data_entry, data_exit, data_sys, temp_prop, extra,
                iterable):

    label = "{0}_{1}".format(iterable[0], iterable[1])
    fast = f"close_sma_{iterable[0]}"
    slow = f"close_sma_{iterable[1]}"
    train_sample_size = 500
    test_sample_size = 50
    print(label)

    sys_signals = evaluate.Signals.set_stop_signals(
        data_mid, data_entry, data_exit, data_sys[[fast, slow]].copy(), fast,
        slow, trade="buy", diff_SL=-0.5)

    sys_signals["label"] = label

    # num_chunks = ((len(sys_signals) - 500) / 100) + 2
    num_chunks = (
        (len(sys_signals) - train_sample_size - test_sample_size) /
        test_sample_size) + 2

    if num_chunks < 1:
        logger.info(f"From {sys_signals['entry_datetime'].iloc[0]} to "
                    f"{sys_signals['entry_datetime'].iloc[-1]}, {label} "
                    f"generated insufficient signals.")
        return None

    properties = temp_prop.merge(
        extra[
            [f"{fast}_close_diff%", f"{slow}_close_diff%", "close_diff_v_atr"]
        ], how="left", left_index=True, right_index=True, validate="1:1")

    properties = properties.shift(1)

    chunks = []
    for ind in range(int(num_chunks)):
        # chunks.append((ind * 100, ind * 100 + 499))
        chunks.append(
            (ind * test_sample_size, ind * test_sample_size +
             train_sample_size + test_sample_size))

    predictions = workshop.ParallelWorker(
        predict_signal, "iterable", label, sys_signals, fast, slow,
        properties, train_sample_size, iterable=chunks).prl()

    with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        try:
            store.append(
                f"predictions/{label}", pd.concat(
                    [df for df in predictions if df is not None], axis=0))
        except ValueError:
            pass


def predict_signal(label, sys_signals, fast, slow, properties,
                   train_sample_size, iterable=None):
    """
    Function to calculate the performance of a trading system, and if the win
    rate is greater then 40%, enhance the system with a random forest model
    that learns from the indicator values calculated for the immediate and
    complete, prior trading session.

    Parameters
    ----------
    label : str
        The name defining the base trading system. Where a simple moving
        average crossover is used, the nomenclature with be 'fast_slow' where
        fast is the number defining the lookback period range used to
        calculate the fast moving average, and the slow is the equivalent for
        the slow moving aveage.

    sys_signals : pandas.core.frame.DataFrame
        The dataframe that contains the entry and exit signals for the trades
        generated by the base system, e.g. SMA crossover.

    fast : str
        The column name for the fast signal line that makes up one component of
        the crossover system.

    slow : str
        The column name for the slow signal line that makes up the other
        component of the crossover system.

    properties : pandas.core.frame.DataFrame
        The dataframe that will contain the indicator values that will be
        associated with the trades respective to timestamp, for the random
        forest model to learn from.

    train_sample_size : int
        The number of samples to use from the dataset to train and evaluate the
        random forest model. The surplus trades will be used a 'live' data,
        where the model will predict whether a trade should be entered or not.
        These prediction would then be evaluated against the original system's
        trades to assess whether the model improved the system or not.

    iterable : tuple
        A tuple with index values that specify a subset from the total system
        signals generated.
    """
    data = sys_signals[iterable[0]:iterable[1]].copy()
    if len(data) <= (train_sample_size + 1):
        logger.info(
            "{} ({} {}) not tested because no test trades to predict".format(
                label, iterable[0], iterable[1]))
        return None
    data.reset_index(drop=True, inplace=True)

    results = count(data)
    performance = calculator.performance_stats(results[0:train_sample_size])

    if performance["win_%"] < 20.:
        logger.info(
            "{} ({} {}) from {} to {} not tested, prior {} signals "
            "yielded less than 20% win rate".format(
                label, iterable[0], iterable[1],
                data["entry_datetime"].iloc[train_sample_size],
                data["entry_datetime"].iloc[-1], train_sample_size))
        return None

    else:
        results["win_loss"] = np.where(results["P/L AUD"] > 0, 1, 0)
        temp_results = results[["entry_datetime", "win_loss"]].copy()
        temp_results.set_index("entry_datetime", inplace=True)

        results_with_properties = temp_results.merge(
            properties, how="left", left_index=True,
            right_index=True, validate="1:1")
        results_with_properties.dropna(inplace=True)

        prediction_results, win_rate, all_feature_score, top_feature_score = \
            machine_learn.predict(results_with_properties, train_sample_size)

        if prediction_results is not None:

            prediction_en_ex = sys_signals[
                sys_signals["entry_datetime"].isin(prediction_results.index)
            ].copy()

            prediction_en_ex_prop = \
                prediction_en_ex.merge(
                    properties, how="left", right_index=True,
                    left_on="entry_datetime", validate="1:1")

            for heading in prediction_en_ex_prop.columns:
                if "iky_cat" in heading:
                    prediction_en_ex_prop[heading] = \
                        prediction_en_ex_prop[heading].astype(str)

            prediction_en_ex_prop.reset_index(drop=True, inplace=True)

            try:
                prediction_results = count(prediction_en_ex)
            except ValueError:
                print(prediction_en_ex)
                return None

            performance_results = \
                calculator.performance_stats(prediction_results)

            logger.info(
                "{} ({} {}) from {} to {} tested, machine learning predicts "
                "{}% win rate, true {}% win rate realised a ${} net "
                "profit. All feature model score: {}, & top feature model "
                "score: {}".format(
                    label, iterable[0], iterable[1],
                    data["entry_datetime"].iloc[train_sample_size],
                    data["entry_datetime"].iloc[-1], win_rate,
                    performance_results["win_%"],
                    performance_results["net_profit"], all_feature_score,
                    top_feature_score))
            return prediction_en_ex_prop
        else:
            logger.info(
                "{} ({} {}) from {} to {} not traded, machine learning "
                "predicts sub 70% ({}%) win rate. All feature model score: "
                "{}, & top feature model score: {}.".format(
                    label, iterable[0], iterable[1],
                    data["entry_datetime"].iloc[train_sample_size],
                    data["entry_datetime"].iloc[-1], win_rate,
                    all_feature_score, top_feature_score))
            return None


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def main():

    pd.set_option("display.max_columns", 35)
    pd.set_option('max_colwidth', 150)
    pd.set_option("display.max_rows", 50)

    # periods = list(range(3, 101, 1))
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    s = [(i, j) for i in periods for j in periods if i < (j - 1)]
    parts = list(split(s, 8))

    with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        data_mid = store["data_mid"]
        data_entry = store["data_ask"]
        data_exit = store["data_bid"]
        data_sys = store["sma_x_y"]
        prop_M15 = store["properties"]
        extra = store["properties_extra"]

    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        prop_H1 = store["properties"]

    prop = prop_M15.merge(
        prop_H1, how="left", left_index=True, right_index=True,
        suffixes=("_M15", "_H1"))
    prop.fillna(method="ffill", inplace=True)

    for combinations in [(12, 24)]:  # tqdm(parts[7]):  # [(66, 72), (70, 75)]
        gen_signals(
            data_mid, data_entry, data_exit, data_sys, prop, extra,
            combinations)


if __name__ == "__main__":

    import sys
    main()
    sys.exit()
    with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        machine_learn_results = count_unrealised(
            store["data_mid"], store["predictions"])
    print(
        machine_learn_results[~machine_learn_results["P/L PIPS"].isnull()])
    machine_learn_results["P/L REALISED"].plot()
    plt.show()

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
