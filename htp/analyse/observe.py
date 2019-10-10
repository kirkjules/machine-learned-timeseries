import numpy as np
import pandas as pd


def close_in_atr(mid, indicator):
    """Function to distinguish price movements between session that exceed
    the ATR."""

    atr = indicator["ATR"].copy().to_frame()
    close_difference = mid["close"].diff().abs().to_frame().\
        rename(columns={"close": "close_difference"})
    compare = atr.merge(
        close_difference, how="left", left_index=True, right_index=True,
        validate="1:1")
    compare["close_in_atr"] = np.where(
        compare["close_difference"] > compare["ATR"], 1, 0)

    return compare["close_in_atr"].to_frame().copy()


def close_to_signal_by_atr(mid, signal, signal_label, indicator):
    """Function to define close to signal distance, quantified in ATR units."""

    compare = pd.concat(
        [mid["close"].to_frame(), signal[signal_label].to_frame(),
         indicator["ATR"].to_frame()],
        axis=1)
    compare["close_to_signal"] = (
        compare["close"] - compare[signal_label]).abs()
    compare["close_to_signal_by_atr"] = (
        compare["close_to_signal"] / compare["ATR"]).round(2)

    return compare["close_to_signal_by_atr"].to_frame().copy()
