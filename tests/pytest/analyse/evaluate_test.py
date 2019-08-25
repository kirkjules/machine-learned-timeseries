import copy
import pytest
import pandas
import loguru
from htp import runner
from htp.api import oanda
from htp.analyse import indicator, evaluate

loguru.logger.enable("htp.api.oanda")


@pytest.fixture
def setup():
    """
    Fixture to establish initialise setup data.
    """
    func = oanda.Candles.to_df
    instrument = "AUD_JPY"
    queryParameters = {
        "from": "2012-01-01 17:00:00", "to": "2012-03-27 17:00:00",
        "granularity": "H1", "price": "M"}
    return {"func": func, "instrument": instrument, "queryParameters":
            queryParameters}


@pytest.fixture
def dataset(setup):
    """
    Fixture to call and return ticker price data.
    """
    data_mid = runner.setup(
        func=setup["func"], instrument=setup["instrument"],
        queryParameters=setup["queryParameters"])
    qP_ask = copy.deepcopy(setup["queryParameters"])
    qP_ask["price"] = "A"
    data_ask = runner.setup(
        func=setup["func"], instrument=setup["instrument"],
        queryParameters=qP_ask)
    qP_bid = copy.deepcopy(setup["queryParameters"])
    qP_bid["price"] = "B"
    data_bid = runner.setup(
        func=setup["func"], instrument=setup["instrument"],
        queryParameters=qP_bid)
    data_prop = indicator.Momentum(data_mid)
    sma_6 = indicator.smooth_moving_average(data_mid, period=6)
    sma_6_24 = indicator.smooth_moving_average(data_mid, df2=sma_6, period=24,
                                               concat=True)

    return {"data_mid": data_mid, "data_ask": data_ask, "data_bid": data_bid,
            "data_sys": sma_6_24, "data_prop": data_prop.atr}


def test_logic(dataset):
    trade_data = evaluate.Signals.sys_signals(
        dataset["data_mid"], dataset["data_ask"], dataset["data_bid"],
        dataset["data_sys"], "close_sma_6", "close_sma_24", trade="buy",
        diff_SL=-0.2)
    test_trade_logic = trade_data["entry_datetime"] < \
            trade_data["exit_datetime"]
    test_trade_to_trade = trade_data["entry_datetime"] > \
            trade_data["exit_datetime"].shift(1)
    test_trade_to_trade.drop(0, axis=0, inplace=True)
    assert all(test_trade_logic.to_numpy()) is True
    assert all(test_trade_to_trade.to_numpy()) is True
