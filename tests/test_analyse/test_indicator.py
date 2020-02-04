import pytest
import numpy as np
import pandas as pd
import tulipy as ti
from htp.analyse import indicator
# from memory_profiler import profile


@pytest.fixture
def data(df):
    ts = df(
        'AUD_JPY',
        {'from': '2018-02-01T13:00:00.000000000Z', 'smooth': True,
         'to': '2018-06-01T13:00:00.000000000Z', 'granularity': 'H1',
         'price': 'M'})
    return ts


def test_sma_method(data):
    """Compare indicator.sma function to Tulipy library."""
    arr = data["close"].to_numpy(copy=True).astype(float)
    ti_sma = np.append([np.nan for i in range(9)], ti.sma(arr, period=10))
    pd_sma = pd.Series(arr).rolling(10).mean()
    assert np.allclose(ti_sma, pd_sma, equal_nan=True)


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
    df_og = data.copy()
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
    df_og = data.copy()
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
    df_og = data.copy()
    d = indicator.Indicate(data=data)
    df_proc = pd.DataFrame(d.data)
    df_og.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_og, df_proc)
