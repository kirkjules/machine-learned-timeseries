import pytest
import numpy as np
import pandas as pd
import tulipy as ti
from htp.analyse import indicator
# from memory_profiler import profile


def test_sma_method(data):
    """Compare indicator.sma function to Tulipy library."""
    arr = data["close"].to_numpy(copy=True).astype(float)
    ti_sma = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    pd_sma = pd.Series(arr).rolling(10).mean().to_numpy()
    assert np.allclose(ti_sma, pd_sma, equal_nan=True)


def test_sma(data):
    arr = data["close"].to_numpy(copy=True).astype(float)
    ti_sma = np.round(
        np.append([np.nan for i in range(9)], ti.sma(arr, period=10)),
        decimals=3)
    sma = indicator.Indicate(data["close"])\
        .smooth_moving_average(10)['close_sma_10']\
        .astype(float)
    assert np.allclose(ti_sma, sma, atol=1e-03, equal_nan=True)


def test_atr(data):
    arr_high = data["high"].to_numpy().astype(float)
    arr_low = data["low"].to_numpy().astype(float)
    arr_close = data["close"].to_numpy().astype(float)
    ti_atr = np.round(
        np.append([np.nan for i in range(13)], ti.atr(
            arr_high, arr_low, arr_close, period=14)),
        decimals=3)
    atr = indicator.Indicate(data)\
        .average_true_range()['atr']\
        .astype(float)
    assert np.allclose(ti_atr, atr, atol=1e-03, equal_nan=True)


@pytest.mark.xfail
def test_adx(data):
    """Spot check against ti seems accurate, slight differences (1e-02) with
    Oanda display"""
    arr_high = data["high"].to_numpy().astype(float)
    arr_low = data["low"].to_numpy().astype(float)
    arr_close = data["close"].to_numpy().astype(float)
    ti_adx = np.append([np.nan for i in range(26)], ti.adx(
        arr_high, arr_low, arr_close, period=14))
    adx = indicator.Indicate(data, exp=6)\
        .average_directional_movement()['adx']\
        .astype(float)
    assert np.allclose(ti_adx[-10:], adx[-10:], atol=1e-03, equal_nan=True)


def test_rsi(data):
    arr = data["close"].to_numpy(copy=True).astype(float)
    ti_rsi = np.round(ti.rsi(arr, 14), decimals=3)
    rsi = indicator.Indicate(data["close"]).relative_strength_index()['rsi']\
        .astype(float)
    assert np.allclose(ti_rsi[-250:], rsi[-250:], atol=1e-03, equal_nan=True)


@pytest.mark.xfail
def test_macd(data):
    """Values match approx Oanda via spot check but not tulipy, hence marked to
    fail"""
    arr = data["close"].to_numpy(copy=True).astype(float)
    ti_macd, ti_signal, ti_histogram = ti.macd(arr, 12, 26, 9)
    s = indicator.Indicate(data["close"], exp=6)\
        .moving_average_convergence_divergence()
    assert np.allclose(ti_macd[-250:], s['macd'][-250:].astype(float),
                       atol=1e-05, equal_nan=True)
    assert np.allclose(ti_signal[-250:], s['signal'][-250:].astype(float),
                       atol=1e-05, equal_nan=True)
    assert np.allclose(
        ti_histogram[-250:], s['histogram'][-250:].astype(float), atol=1e-05,
        equal_nan=True)


def test_stoch(data):
    arr_high = data["high"].to_numpy().astype(float)
    arr_low = data["low"].to_numpy().astype(float)
    arr_close = data["close"].to_numpy().astype(float)
    ti_percK, ti_percD = ti.stoch(arr_high, arr_low, arr_close, 14, 1, 3)
    stoch = indicator.Indicate(data).stochastic()
    percK = stoch['percK'].astype(float)
    percD = stoch['percD'].astype(float)
    assert np.allclose(
        ti_percK[-250:], percK[-250:], atol=1e-03, equal_nan=True)
    assert np.allclose(
        ti_percD[-250:], percD[-250:], atol=1e-03, equal_nan=True)


@pytest.mark.xfail(raises=ValueError)
def test_indicate_init_none():
    indicator.Indicate()


@pytest.mark.parametrize(
    'ts, labels, orient',
    [pytest.param(
         ['83.45', '83.42', '83.67'], None, 'rows', marks=pytest.mark.xfail(
             raises=TypeError)),
     pytest.param(
         [['83.45', '84.00'], ['84.5']], None, 'rows', marks=pytest.mark.xfail(
             raises=ValueError)),
     pytest.param(
         [['86.73', '86.84'], ['86.88', '86.95']], ['open'], 'rows',
         marks=pytest.mark.xfail(raises=ValueError)),
     ([['82.02', '81.99']], ['open'], 'rows'),
     ([['83.45', '84.00'], ['82.02', '81.99']], ['open', 'high'], 'rows'),
     pytest.param(pd.Series(['83.45', '84.00']), None, 'rows',
                  marks=pytest.mark.xfail(raises=ValueError)),
     pytest.param(pd.Series(['83.45', '84.00']), ['open', 'high'], 'rows',
                  marks=pytest.mark.xfail(raises=ValueError)),
     (pd.Series(['83.45', '84.00']), ['open'], 'rows'),
     ])
def test_indicate_init(ts, labels, orient):
    d = indicator.Indicate(data=ts, labels=labels, orient=orient)
    assert isinstance(d.data, dict)


@pytest.mark.xfail(raises=ValueError)
def test_indicate_init_np_rows(data):
    ts = data.to_numpy()
    indicator.Indicate(data=ts, labels=['open', 'high', 'low'], orient='rows')


def test_indicate_init_np_rows_integrity(data):
    df_og = data.astype(float).copy()
    ts = data.to_numpy()
    d = indicator.Indicate(
        data=ts, labels=['open', 'high', 'low', 'close'], orient='rows')
    df_proc = pd.DataFrame(d.data)
    df_og.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_og, df_proc)


@pytest.mark.xfail(raises=ValueError)
def test_indicate_init_np_columns(data):
    ts = data.to_numpy()
    columns = np.split(ts, ts.shape[1], axis=1)
    del ts
    ts = np.asarray([np.concatenate(col) for col in columns])
    indicator.Indicate(data=ts, labels=['open', 'high', 'low'],
                       orient='columns')


def test_indicate_init_np_columns_integrity(data):
    df_og = data.astype(float).copy()
    ts = data.to_numpy()
    columns = np.split(ts, ts.shape[1], axis=1)
    del ts
    ts = np.asarray([np.concatenate(col) for col in columns])
    d = indicator.Indicate(data=ts, labels=['open', 'high', 'low', 'close'],
                           orient='columns')
    df_proc = pd.DataFrame(d.data)
    df_og.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_og, df_proc)


def test_indicate_init_df_integrity(data):
    df_og = data.astype(float).copy()
    d = indicator.Indicate(data=data)
    df_proc = pd.DataFrame(d.data)
    df_og.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_og, df_proc)
