import pytest
import pandas as pd
from htp.analyse import evaluate, indicator, signal


@pytest.fixture
def mid(df):
    ts = df(
        'AUD_JPY',
        {'count': 5000, 'smooth': True, 'granularity': 'H1', 'price': 'M'})
    return ts


@pytest.fixture
def ask(df):
    ts = df(
        'AUD_JPY',
        {'count': 5000, 'smooth': True, 'granularity': 'H1', 'price': 'A'})
    return ts


@pytest.fixture
def bid(df):
    ts = df(
        'AUD_JPY',
        {'count': 5000, 'smooth': True, 'granularity': 'H1', 'price': 'B'})
    return ts


@pytest.fixture
def indicate(mid):
    return indicator.Indicate(mid)


@pytest.fixture
def sys(indicate):
    atr = indicate.average_true_range()
    sma_4 = indicate.smooth_moving_average(4)
    sma_24 = indicate.smooth_moving_average(24)
    atr.update(sma_4)
    atr.update(sma_24)
    return pd.DataFrame(atr, index=mid.index).astype(float)


def test_evaluate_v_signal_init(mid, ask, bid, sys):
    """Test numpy optimised logic vs original pandas implementation for init
    functionality."""
    s1 = evaluate.Signals(mid, ask, bid, sys, 'close_sma_4', 'close_sma_24')
    print(s1.raw_signals.tail(50))

    ask.rename(columns={'open': 'entry_open', 'high': 'entry_high', 'low':
                        'entry_low', 'close': 'entry_close'}, inplace=True)
    bid.rename(columns={'open': 'exit_open', 'high': 'exit_high', 'low':
                        'exit_low', 'close': 'exit_close'}, inplace=True)
    df = pd.concat([mid, ask, bid, sys], axis=1).astype(float)
    s2 = signal.Signals(df, 'close_sma_4', 'close_sma_24')
    print(s2.raw_signals.tail(50))


def test_evaluate_v_signal_system_trades(mid, ask, bid, sys):
    """Test pandas vectorised implementation vs original iterative logic for
    generating system trades."""
    s1 = evaluate.Signals.sys_signals(
        mid, ask, bid, sys, 'close_sma_4', 'close_sma_24')
    s1['entry_price'] = s1['entry_price'].astype(float)
    s1['exit_price'] = s1['exit_price'].astype(float)
    ask.rename(columns={'open': 'entry_open', 'high': 'entry_high', 'low':
                        'entry_low', 'close': 'entry_close'}, inplace=True)
    bid.rename(columns={'open': 'exit_open', 'high': 'exit_high', 'low':
                        'exit_low', 'close': 'exit_close'}, inplace=True)
    df = pd.concat([mid, ask, bid, sys], axis=1).astype(float)
    s2 = signal.Signals.system(df, 'close_sma_4', 'close_sma_24')
    pd.testing.assert_frame_equal(s1.head(10), s2.head(10))


def test_signal_system_trades_business_logic(prep):
    """Test resulting trade business logic, e.g. entry chronologically before
    exit etc."""
    pass
