import pytest
import pandas
import numpy as np
from htp import runner
from htp.api import oanda


@pytest.fixture
def dataset():
    func = oanda.Candles.to_df
    instrument = "AUD_JPY"
    queryParameters = {
        "from": "2012-01-01 17:00:00", "to": "2012-06-27 17:00:00",
        "granularity": "H1", "price": "M"}
    return {"func": func, "instrument": instrument, "queryParameters":
            queryParameters}


@pytest.fixture
def data_mid(dataset):
    """
    Fixture to call and return ticker mid price data.
    """
    return runner.setup(
        func=dataset["func"], instrument=dataset["instrument"],
        queryParameters=dataset["queryParameters"])


def test_fixtures(data_mid):
    data = data_mid
    print(data.head())
    assert type(data) == pandas.core.frame.DataFrame

