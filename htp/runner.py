import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from loguru import logger
from decimal import Decimal
from pprint import pprint
from htp.toolbox import calculator, workshop
from htp.analyse import evaluate, predict


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
    RISK_PERC = 0.01
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
                    Decimal(AMOUNT) * Decimal(0.01)).quantize(Decimal(".01"))
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


# def win_loss(row):
#     if row["P/L AUD"] >= 0:
#         return 1
#     else:
#         return 0


def gen_signals(data_mid, data_entry, data_exit, data_sys, temp_prop, extra,
                iterable):

    label = "{0}_{1}".format(iterable[0], iterable[1])
    fast = f"close_sma_{iterable[0]}"
    slow = f"close_sma_{iterable[1]}"

    print(label)
    sys_signals = evaluate.Signals.sys_signals(
        data_mid, data_entry, data_exit, data_sys[[fast, slow]].copy(), fast,
        slow, trade="buy", diff_SL=-0.2)

    sys_signals["label"] = label

    num_chunks = ((len(sys_signals) - 500) / 100) + 2

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
        chunks.append((ind * 100, ind * 100 + 499))

    predictions = workshop.ParallelWorker(
        predict_signal, "iterable", label, sys_signals, fast, slow,
        properties, iterable=chunks).prl()

    with pd.HDFStore("data/AUD_JPY.h5") as store:
        try:
            store.append(
                "predictions", pd.concat(
                    [df for df in predictions if df is not None], axis=0))
        except ValueError:
            pass


def predict_signal(label, sys_signals, fast, slow, properties, iterable=None):

    logger.info("{} {} to {}".format(label, iterable[0], iterable[1]))

    data = sys_signals[iterable[0]:iterable[1]].copy()
    data.reset_index(drop=True, inplace=True)

    # check_results = runner.count(data[0:400].copy())
    # performance = calculator.performance_stats(check_results)

    results = count(data)
    performance = calculator.performance_stats(results[0:400])

    if performance["win_%"] < 25:
        logger.info(
            "{} from {} to {} not tested, prior 400 signals "
            "yielded less than 40% win rate".format(
                label, data["entry_datetime"].iloc[400],
                data["entry_datetime"].iloc[-1]))
        return None

    else:
        # results = count(data)
        # results["win_loss"] = results.apply(win_loss, axis=1)
        results["win_loss"] = np.where(results["P/L AUD"] > 0, 1, 0)
        temp_results = results[["entry_datetime", "win_loss"]].copy()
        temp_results.set_index("entry_datetime", inplace=True)

        # sma_open = pd.concat(
        #     [data_mid["open"], temp_prop["ATR"], data_sys.shift(1)],
        #     axis=1)
        # sma_open["open_diff"] = sma_open["open"] - \
        #     sma_open["open"].shift(1)
        # sma_open["open_diff_v_atr"] = sma_open.apply(
        #     lambda x: 1 if x["open_diff"] > x["ATR"] else 0, axis=1)

        # for i in [fast, slow]:
        #     sma_open[f"{i}_open_diff%"] = \
        #        (sma_open["open"] - sma_open[i]) / \
        #         sma_open["open"] * \
        #         100

        # properties = temp_prop.merge(
        #     sma_open[[f"{fast}_open_diff%",
        #               f"{slow}_open_diff%",
        #               "open_diff_v_atr"]],  # , "open", "close_sma_6"]],
        #     how="left", left_index=True, right_index=True, validate="1:1")
        # properties.drop("ATR", axis=1, inplace=True)

        results_with_properties = temp_results.merge(
            properties, how="left", left_index=True,
            right_index=True, validate="1:1")
        results_with_properties.dropna(inplace=True)
        # results_with_properties.reset_index(drop=True, inplace=True)

        prediction_results, win_rate = \
            predict.random_forest(results_with_properties)

        if prediction_results is not None:

            # prediction_entry_exit = prediction_results.merge(
            #     sys_signals, how="left", left_index=True,
            #     right_on="entry_datetime", validate="1:1").reset_index(
            #         drop=True)

            prediction_en_ex = sys_signals[
                sys_signals["entry_datetime"].isin(prediction_results.index)
            ].copy()

            prediction_en_ex_prop = \
                prediction_en_ex.merge(
                    properties, how="left", right_index=True,
                    left_on="entry_datetime", validate="1:1")

            prediction_en_ex_prop["iky_cat"] = \
                prediction_en_ex_prop["iky_cat"].astype(str)
            prediction_en_ex_prop.reset_index(drop=True, inplace=True)

            logger.info(
                "{} from {} to {} tested, machine learning predicts "
                "{}% win rate".format(
                    label, data["entry_datetime"].iloc[400],
                    data["entry_datetime"].iloc[-1], win_rate))
            return prediction_en_ex_prop
        else:
            logger.info(
                "{} from {} to {} not traded, machine learning predicts "
                "sub {}% win rate".format(
                    label, data["entry_datetime"].iloc[400],
                    data["entry_datetime"].iloc[-1], win_rate))
            return None


def main():

    pd.set_option("display.max_columns", 16)
    pd.set_option('max_colwidth', 150)
    pd.set_option("display.max_rows", 50)

    # periods = list(range(3, 101, 1)
    # s = [(i, j) for i in periods for j in periods if i < j]

    with pd.HDFStore("data/AUD_JPY.h5") as store:
        data_mid = store["data_mid"]
        data_entry = store["data_ask"]
        data_exit = store["data_bid"]
        data_sys = store["sma_x_y"]
        prop = store["properties"]
        extra = store["properties_extra"]

    for combinations in tqdm([(24, 48), (48, 96)]):
        gen_signals(
            data_mid, data_entry, data_exit, data_sys, prop, extra,
            combinations)


if __name__ == "__main__":

    # import sys
    main()
    # sys.exit()
    with pd.HDFStore("data/AUD_JPY.h5") as store:
        # linear_results = count_v2(store["data_mid"], store["base_line"])
        machine_learn_results = count_unrealised(
            store["data_mid"], store["predictions"])
    # print(
    #     linear_results[~linear_results["P/L PIPS"].isnull()])
    # linear_results["P/L REALISED"].plot()
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
