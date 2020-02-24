import numpy as np
# import pandas as pd


def close_in_atr(close, atr):
    """Function to distinguish price movements between session that exceed
    the ATR."""
    close_difference = np.absolute(close - np.roll(close, 1))
    close_in_atr = np.where(close_difference > atr, 1, 0)
    return close_in_atr


def close_to_signal_by_atr(close, signal, atr):
    """Function to define close to signal distance, quantified in ATR units."""
    close_to_signal = np.absolute(close - signal)
    close_to_signal_by_atr = close_to_signal / atr
    return close_to_signal_by_atr


def trend_ichimoku(close, **ichimoku_cloud):
    """Function to define a switch between an up or down trend in a financial
    timeseries based on the Ichimoku Cloud indicator."""
    trend = np.where(np.greater(close, ichimoku_cloud['tenkan']), 1, -1)
    up = (trend == 1)
    down = (trend == -1)
    tenkan_kijun = np.greater(
        ichimoku_cloud['tenkan'], ichimoku_cloud['kijun'])
    trend[down][tenkan_kijun] = 0
    trend[up][~tenkan_kijun] = 0
    return trend


def trend_convergence_divergence(**MACD):
    """Function to define a switch between an up or down trend in a financial
    timeseries based on the MACD indicator."""
    trend = np.where(MACD['histogram'] > 0., 1, -1)
    return trend


def trend_relative_strength_index(RSI):
    """Function to define a switch between an up or down trend in a financial
    timeseries based on the Relative Strength Index indicator."""
    with np.nditer([RSI['rsi'].astype(float), None]) as it:
        oversold = 0
        overbought = 0
        for x, y in it:
            if x > 70.:
                overbought = 1
                oversold = 0
                y[...] = 0
            elif x < 30.:
                overbought = 0
                oversold = 1
                y[...] = 0
            elif 70. > x > 50.:
                if overbought == 1:
                    y[...] = 0
                else:
                    oversold = 0
                    y[...] = 1
            elif 50. > x > 30.:
                if oversold == 1:
                    y[...] = 0
                else:
                    overbought = 0
                    y[...] = -1
            # else:
            #     y[...] = 0
        return it.operands[1]


def trend_stochastic(**stochastic):
    """Function to define a switch between an up or down trend in a financial
    timeseries based on the Stochastic indicator."""
    trend = np.zeros(len(stochastic['percK']))
    up = np.where(
        stochastic['percK'] < 20. and stochastic['percD'] < 20., True, False)
    down = np.where(
        stochastic['percK'] > 80. and stochastic['percD'] > 80., True, False)
    trend[up] = 1
    trend[down] = -1
    return trend


def trend_directional_movement(ADX):
    trend = np.zeros(len(ADX['adx']))
    strong = np.greater(ADX['adx'], 50.)
    weak = np.less(ADX['adx'], 20.)
    trend[strong] = 1
    trend[weak] = -1
    return trend
