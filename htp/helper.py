import numpy as np
import pandas as pd
from tqdm import tqdm
from loguru import logger
from htp.analyse import evaluate, indicator

logger.enable("htp.api.oanda")


def main(data_mid):

    # periods = list(range(3, 101, 1))
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in tqdm(periods):
        avg = indicator.smooth_moving_average(
            data_mid, column="close", period=i)
        avgs.append(avg)
    sma_x_y = pd.concat(avgs, axis=1)
    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("sma_x_y", sma_x_y)

    # PROPERTIES --> object: data_temp
    iky = indicator.ichimoku_kinko_hyo(data_mid)
    iky_close = pd.concat([iky[["tenkan", "kijun", "senkou_A", "senkou_B"]],
                           data_mid["close"]], axis=1)
    iky_close["iky_cat"] = iky_close.apply(evaluate.iky_cat, axis=1)

    rsi = indicator.relative_strength_index(data_mid)

    stoch = indicator.stochastic(data_mid)
    stoch["stoch_diff"] = stoch["%K"] - stoch["%D"]

    macd = indicator.moving_average_convergence_divergence(data_mid)

    adx = indicator.Momentum.average_directional_movement(data_mid)

    atr = indicator.Momentum.average_true_range(data_mid)

    data_properties = pd.concat(
        [iky_close["iky_cat"], rsi["RSI"], adx["ADX"],
         stoch[["%K", "%D", "stoch_diff"]], atr["ATR"],
         macd[["MACD", "Signal", "Histogram"]]], axis=1)

    with pd.HDFStore("data/AUD_JPY_H1.h5") as store:
        store.append("properties", data_properties)

    # to-do
    sma_close = pd.concat(
        [data_mid["close"], data_properties["ATR"], sma_x_y], axis=1)
    sma_close["close_diff"] = sma_close["close"] - sma_close["close"].shift(1)
    sma_close["close_diff_v_atr"] = np.where(
        sma_close["close_diff"].abs() > sma_close["ATR"], 1, 0)
    for i in sma_x_y.columns:
        sma_close[f"{i}_close_diff%"] =\
                (sma_close["close"] - sma_close[i]) /\
                sma_close["close"] *\
                100
        sma_close.drop(i, axis=1, inplace=True)
    sma_close.drop(["close", "ATR", "close_diff"], axis=1, inplace=True)
    sma_close = sma_close.round(4)


if __name__ == "__main__":
    main()
