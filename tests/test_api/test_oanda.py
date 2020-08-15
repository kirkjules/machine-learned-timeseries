import os
import pandas
import pytest
from htp.api import exceptions
from htp.api.oanda import Candles


@pytest.fixture
def get_data():
    """Initiate a new query to the Oanda API end-point and return the result
    for inspection."""
    return Candles(instrument='AUD_JPY', queryParameters={'count': 6})


def test_auth_token(get_data):
    """Test to confirm accurate parsing of auth token from env files by Api
    class, through the inherting Candles class."""
    assert os.environ['OANDA_PRACTISE_TOKEN'] in\
        get_data.headers['Authorization']


def test_request_200(get_data):
    """Test that the Candles class sends a GET request and receives a
    successful response."""
    assert get_data.r.status_code == 200


def test_data_shape(get_data):
    """Test to confirm the returned data matches the expected size."""
    assert len(get_data.r.json()['candles']) ==\
        get_data.queryParameters['count']


def test_api_error_handling():
    """Test to confirm the capture and raise of a invalid symbol request."""
    with pytest.raises(exceptions.ApiError):
        Candles(instrument='XYZ_ABC', queryParameters={'count': 6})


@pytest.fixture
def to_df(get_data):
    """Initiates a new query to the Oanda API end-point and manipulates the
    received json data into a pandas dataframe."""
    return Candles.to_df(get_data.r.json(), 'M')


def test_json_to_df_shape(to_df, get_data):
    """Test the data manipulation preserves the expected data size."""
    assert len(to_df.index) == get_data.queryParameters['count']


def test_json_to_df_index(to_df):
    """Test the data manipulation successfully converts time values into a time
    format."""
    assert type(to_df.index) == pandas.core.indexes.datetimes.DatetimeIndex
