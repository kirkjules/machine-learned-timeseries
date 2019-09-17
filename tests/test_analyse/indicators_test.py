import pytest
import pandas
import numpy as np
import tulipy as ti
from htp.analyse import indicator
from memory_profiler import profile


@pytest.fixture
@profile
def sma(setup):
    return indicator.smooth_moving_average(setup)


def test_sma(sma):
    assert type(sma) == pandas.core.frame.DataFrame


def test_tulipy_sma(setup, sma):
    """
    Compare tulipy sma return values to indicator.sma function.

    Note, tulipy results are explicitly converted into dataframe to be indexed,
    therefore standardised against the control (indicator.<func>) values that
    are calculated against the index in a pure pandas solution.
    """
    arr = setup["close"].to_numpy(copy=True).astype(float)
    ind = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    df = pandas.DataFrame({
        "close_sma_10": pandas.Series(ind, index=setup.index)}).round(3)
    assert len(arr) == len(df)
    assert np.array_equal(
        df["close_sma_10"].to_numpy(copy=True).astype(float)[9:20],
        sma["close_sma_10"].to_numpy(copy=True).astype(float)[9:20])
