import pytest
from htp.api import oanda


@pytest.fixture
def number():
    return 5


@pytest.fixture
def df():
    """Generate test candle data to use as a standard fixture."""

    def _get(ticker, queryParameters):
        return oanda.Candles.to_df(
            oanda.Candles(instrument=ticker, queryParameters=queryParameters
                          ).r.json(), queryParameters['price'])

    return _get
