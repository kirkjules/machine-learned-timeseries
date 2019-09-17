import pytest
import pandas
import numpy as np
import tulipy as ti
from htp.analyse import indicator
from htp.api.oanda import Candles
from memory_profiler import profile


@pytest.fixture
def local_setup():
    """
    Fixture that is callable by other test function.

    Invoked individually for each calling function.
    """
    arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                 "granularity": "H1", "smooth": True, "count": 2000}
    data = Candles.to_df(instrument="AUD_JPY", queryParameters=arguments)
    return data


@pytest.fixture
@profile
def sma(local_setup):
    return indicator.smooth_moving_average(local_setup)


@pytest.fixture
@profile
def rsi(local_setup):
    return indicator.relative_strength_index(local_setup)


def test_sma(sma):
    assert type(sma) == pandas.core.frame.DataFrame


def test_rsi(rsi):
    assert type(rsi) == pandas.core.frame.DataFrame


def test_tulipy_sma(local_setup, sma):
    """
    Compare tulipy sma return values to indicator.sma function.

    Note, tulipy results are explicitly converted into dataframe to be indexed,
    therefore standardised against the control (indicator.<func>) values that
    are calculated against the index in a pure pandas solution.
    """
    arr = local_setup["close"].to_numpy(copy=True).astype(float)
    ind = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    df = pandas.DataFrame({
        "close_sma_10": pandas.Series(ind, index=local_setup.index)}).round(3)
    assert len(arr) == len(df)
    assert np.array_equal(
        df["close_sma_10"].to_numpy(copy=True).astype(float)[9:20],
        sma["close_sma_10"].to_numpy(copy=True).astype(float)[9:20])


def test_tulipy_rsi(local_setup, rsi):
    """
    Compare tulipy rsi return values to indicator.rsi function.
    """
    arr = local_setup["close"].to_numpy(copy=True).astype(float)
    ind = np.append([np.nan for i in range(14)], ti.rsi(arr, period=14))
    # print(len(ind))
    df = pandas.DataFrame({
        "Tulipy RSI": pandas.Series(ind, index=local_setup.index)}).round(3)
    assert len(arr) == len(df)
    # print(pandas.concat([rsi, df], axis=1).head(20))
    assert np.array_equal(
        df["Tulipy RSI"].to_numpy(copy=True).astype(float)[14:20],
        rsi["RSI"].to_numpy(copy=True).astype(float)[14:20])
