import numpy as np
import pandas as pd


def close_in_atr(mid, atr):
    """Function to distinguish price movements between session that exceed
    the ATR."""

    close_difference = mid["close"].diff().abs().to_frame().\
        rename(columns={"close": "close_difference"})
    compare = atr.merge(
        close_difference, how="left", left_index=True, right_index=True,
        validate="1:1")
    compare["close_in_atr"] = np.where(
        compare["close_difference"] > compare["atr"], 1, 0)

    return compare["close_in_atr"].to_frame()


def close_to_signal_by_atr(mid, signal, signal_label, atr, speed='fast'):
    """Function to define close to signal distance, quantified in ATR units."""

    compare = pd.concat([mid, signal, atr], axis=1)
    compare["close_to_signal"] = (compare["close"] - compare[signal_label]
                                  ).abs()
    compare["close_to_signal_by_atr"] = (
        compare["close_to_signal"] / compare["atr"]).round(2)

    df = compare["close_to_signal_by_atr"].to_frame()
    df.rename(columns={"close_to_signal_by_atr": f"close_to_{speed}_by_atr"},
              inplace=True)
    return df
