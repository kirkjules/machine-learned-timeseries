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


def test_sma(sma):
    assert type(sma) == pandas.core.frame.DataFrame


def test_tulipy_sma(local_setup, sma):
    """
    Compare tulipy sma return values to indicator.sma function.
    """
    arr = local_setup["close"].to_numpy(copy=True).astype(float)
    ind = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    df = pandas.DataFrame({
        "close_sma_10": pandas.Series(ind, index=local_setup.index)}).round(3)
    assert len(arr) == len(df)
    assert np.array_equal(
        df["close_sma_10"].to_numpy(copy=True).astype(float)[9:20],
        sma["close_sma_10"].to_numpy(copy=True).astype(float)[9:20])
