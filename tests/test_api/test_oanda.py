import os
import pandas
import pytest
from htp.api import exceptions
from htp.api.oanda import Candles


@pytest.fixture
def get_data():
    return Candles(instrument='AUD_JPY', queryParameters={'count': 6})


def test_auth_token(get_data):
    assert os.environ['OANDA_PRACTISE_TOKEN'] in\
        get_data.headers['Authorization']


def test_request_200(get_data):
    assert get_data.r.status_code == 200


def test_data_shape(get_data):
    assert len(get_data.r.json()['candles']) ==\
        get_data.queryParameters['count']


def test_api_error_handling():
    with pytest.raises(exceptions.ApiError):
        Candles(instrument='XYZ_ABC', queryParameters={'count': 6})


@pytest.fixture
def to_df(get_data):
    return Candles.to_df(get_data.r.json(), 'M')


def test_json_to_df_shape(to_df, get_data):
    assert len(to_df.index) == get_data.queryParameters['count']


def test_json_to_df_index(to_df):
    assert type(to_df.index) == pandas.core.indexes.datetimes.DatetimeIndex
