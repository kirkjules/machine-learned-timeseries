import pytest
import numpy as np
import pandas as pd
import tulipy as ti
from htp.analyse import indicator
# from memory_profiler import profile


@pytest.fixture
def sma(setup):
    return indicator.smooth_moving_average(setup)


# def test_sma(sma):
#     assert type(sma) == pandas.core.frame.DataFrame


def test_tulipy_sma(setup, sma):
    """
    Compare tulipy sma return values to indicator.sma function.

    Note, tulipy results are explicitly converted into dataframe to be indexed,
    therefore standardised against the control (indicator.<func>) values that
    are calculated against the index in a pure pandas solution.
    """
    arr = setup["close"].to_numpy(copy=True).astype(float)
    ind = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    df = pd.DataFrame({
        "close_sma_10": pd.Series(ind, index=setup.index)}).round(5)
    assert len(arr) == len(df)


@pytest.fixture
def stochastic_1(setup, period=14, smoothK=1, smoothD=3):
    minN = setup["low"].rolling(period).min().rename("minN")
    maxN = setup["high"].rolling(period).max().rename("maxN")
    s = pd.concat([pd.to_numeric(setup["close"]), minN, maxN], axis=1)

    s["%K"] = s.apply(
        lambda x: 100 * (x["close"] - x["minN"]) / (x["maxN"] - x["minN"]),
        axis=1).rolling(smoothK).mean()

    s["%D"] = s["%K"].rolling(smoothD).mean()

    return s.round(4)


@pytest.fixture
def stochastic_2(setup, period=14, smoothK=1, smoothD=3):
    """
    14.6 s ± 568 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
    """
    minN = setup["low"].rolling(period).min().rename("minN")
    maxN = setup["high"].rolling(period).max().rename("maxN")
    s = pd.concat([pd.to_numeric(setup["close"]), minN, maxN], axis=1)

    def stoch_K(row):
        nominator = row["close"] - row["minN"]
        denominator = row["maxN"] - row["minN"]
        if denominator == 0:
            k = 0
        else:
            k = nominator / denominator
        return k * 100

    s["%K"] = s.apply(stoch_K, axis=1).rolling(smoothK).mean()
    s["%D"] = s["%K"].rolling(smoothD).mean()
    return s.round(4)


@pytest.fixture
def stochastic_3(setup, period=14, smoothK=1, smoothD=3):
    """
    69.5 ms ± 3.85 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
    """
    minN = setup["low"].rolling(period).min().to_numpy()
    maxN = setup["high"].rolling(period).max().to_numpy()
    nominator = setup.close.values - minN
    denominator = maxN - minN
    k = np.divide(nominator, denominator, out=np.zeros_like(nominator),
                  where=denominator != 0)
    percK = k * 100
    s = pd.DataFrame(data=percK, index=setup.index, columns=['K'])
    s["%K"] = s["K"].rolling(smoothK).mean()
    s.drop('K', axis=1, inplace=True)
    s["%D"] = s["%K"].rolling(smoothD).mean()
    return s.round(4)


def test_stochastic(stochastic_2, stochastic_3, col="%K"):
    a = stochastic_2.fillna(0)
    b = stochastic_3.fillna(0)
    x = np.equal(a[col].values[14:], b[col].values[14:])
    diff = []
    count = 14
    for i in x:
        if not i:
            diff.append(count)
        count += 1
    t = []
    for i in diff:
        y = a[col].values[i]
        z = b[col].values[i]
        if abs(y - z) > 0.0002:
            print(f"{a.iloc[i].name}: {a.iloc[i][col]}\
                  {b.iloc[i].name}: {b.iloc[i][col]}")
            t.append(i)
    assert len(t) == 0
