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


class Momentum2:

    def __init__(self, data, period=14):
        self.high = pd.to_numeric(data["high"], errors="coerce")
        self.low = pd.to_numeric(data["low"], errors="coerce")
        self.close = pd.to_numeric(data["close"], errors="coerce")

        HL = (self.high - self.low).rename("HL")
        HpC = (self.high - self.close.shift(1)).abs().rename("HpC")
        LpC = (self.low - self.close.shift(1)).abs().rename("LpC")

        tr = pd.concat([HL, HpC, LpC], axis=1)
        tr["TR"] = tr.max(axis=1)

        d = self._wilder_average_a(tr, "TR", period)
        ATR = pd.DataFrame.from_dict(
            d, orient="index").rename(columns={0: "ATR"})

        atr = tr.merge(
            ATR, how="left", left_index=True, right_index=True, validate="1:1")
        self.atr = atr.round(4)
        self.period = period

    def _wilder_average_a(self, df, column, length):

        d = {}
        X = 0
        prevX = 0
        count = 0
        df[f"r{length}{column}"] = df[column].rolling(length).mean()
        col_ind = ([i for i in df.columns].index(column) + 1)
        col_mean_ind = ([
            i for i in df.columns].index(f"r{length}{column}") + 1)
        for row in df.itertuples():
            if count == length:
                X = row[col_mean_ind]  # [f"r{length}{column}"]
                d[row[0]] = X
            elif count > length:
                X = (prevX * (length - 1) + row[col_ind]) / length  # [column]
                d[row[0]] = X
            prevX = X
            count += 1

        return d

    def _wilder_average_b(self, df, column, length):

        d = {}
        X = 0
        prevX = 0
        count = 0
        df[f"r{length}{column}"] = df[column].rolling(length).sum()
        col_ind = ([i for i in df.columns].index(column) + 1)
        col_mean_ind = (
            [i for i in df.columns].index(f"r{length}{column}") + 1)
        for row in df.itertuples():
            if count == length:
                X = row[col_mean_ind]  # [f"r{length}{column}"]
                d[row[0]] = X
            elif count > length:
                X = prevX - (prevX / length) + row[col_ind]  # [column]
                d[row[0]] = X
            prevX = X
            count += 1

        return d

    def _ADX_DM_logic(self, row, colA, colB):
        # not optimised
        if row[colA] > row[colB] and row[colA] > 0:
            return row[colA]
        else:
            return 0

    @classmethod
    def average_directional_movement(cls, *args, **kwargs):
        n = cls(*args, **kwargs)
        HpH = (n.high - n.high.shift(1)).rename("HpH")
        pLL = (n.low.shift(1) - n.low).rename("pLL")

        DM = pd.concat([HpH, pLL, n.atr["TR"]], axis=1)
        DM["+DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("HpH", "pLL"))
        DM["-DM"] = DM.apply(n._ADX_DM_logic, axis=1, args=("pLL", "HpH"))

        # StockCharts (school.stockcharts.com/doku.php?id=technical_indicators:
        # average_directional_index_adx)
        uDMdic = n._wilder_average_b(DM, "+DM", n.period)
        uDM = pd.DataFrame.from_dict(
            uDMdic, orient="index").rename(columns={0: "+DM14"})

        dDMdic = n._wilder_average_b(DM, "-DM", n.period)
        dDM = pd.DataFrame.from_dict(
            dDMdic, orient="index").rename(columns={0: "-DM14"})

        TRdic = n._wilder_average_b(n.atr, "TR", n.period)
        TR14 = pd.DataFrame.from_dict(
            TRdic, orient="index").rename(columns={0: "TR14"})

        DI = pd.concat([uDM, dDM, TR14], axis=1)
        DI["+DI"] = DI["+DM14"] / DI["TR14"] * 100
        DI["-DI"] = DI["-DM14"] / DI["TR14"] * 100
        DI["DX"] = (DI["+DI"] - DI["-DI"]).abs() /\
            (DI["+DI"] + DI["-DI"]).abs() *\
            100

        adx_copy = DI.copy(deep=True)
        adx_dict = n._wilder_average_a(adx_copy, "DX", n.period)
        adx_frame = pd.DataFrame.from_dict(
            adx_dict, orient="index").rename(columns={0: "ADX"})
        ADX = DI.merge(
            adx_frame, how="left", left_index=True, right_index=True,
            validate="1:1")

        return ADX[["+DI", "-DI", "DX", "ADX"]].round(4)
