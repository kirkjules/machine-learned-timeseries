import pytest
import requests
import pandas as pd
from celery import chord
from yaml import safe_load
import celery_app.tasks as tasks


def api_get(access, ticker, params, timeout):
    """Helper function to assess error handling. Incorporates code from
    target function."""
    d = tasks.Api(access=access)
    s = requests.Session()
    s.headers.update(
        {"Content-Type": "application/json",
         "Authorization": f"Bearer {d.details['token']}"})
    try:
        r = s.get(
            f'https://api-fxpractice.oanda.com/v3/instruments/'
            f'{ticker}/candles?',
            params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return str(e)
    else:
        if r.status_code != requests.codes.ok:
            return r.json()["errorMessage"]
        else:
            return r.json()


def test_status_code():
    """Test function to assess successful api call."""
    r = tasks.session_get_data(
        "AUD_JPY", params={"count": 5, "granularity": "S5"}, timeout=None)
    assert "errorMessage" not in r[0].keys()


def test_config_load():
    """Test function to access successful config file read through."""
    with open("config.yaml", "r") as f:
        cf = safe_load(f)
    assert "oanda" in cf.keys()


@pytest.mark.parametrize('access', ["invalid_token", "practise"])
@pytest.mark.parametrize('ticker', ["ABC_XYZ"])
@pytest.mark.parametrize('params', [{"count": 5, "granularity": "S5"}])
@pytest.mark.parametrize('timeout', [None])
def test_oanda_error(access, ticker, params, timeout):
    """Test function parametrized to handle Oanda api error resulting from
    invalid token and invalid ticker."""
    r = api_get(access, ticker, params, timeout)
    assert isinstance(r, str)


@pytest.mark.parametrize('access', ["practise"])
@pytest.mark.parametrize('ticker', ["AUD_JPY"])
@pytest.mark.parametrize('params', [{"count": 5, "granularity": "S5"}])
@pytest.mark.parametrize('timeout', [0.001])
def test_api_error(access, ticker, params, timeout):
    """Test function parametrized to handle requests errors arising from
    exceeded timeout."""
    r = api_get(access, ticker, params, timeout)
    assert isinstance(r, str)


@pytest.mark.parametrize('ticker', ["AUD_JPY", "EUR_USD"])
@pytest.mark.parametrize('params', [{"count": 5, "granularity": "S5", "price": "M"}])
@pytest.mark.parametrize('timeout', [10])
def test_session_get_data(ticker, params, timeout):
    r = tasks.session_get_data(ticker, params=params, timeout=timeout)
    assert type(r) == tuple
    assert len(r[0]) == params["count"]

# requires celery: celery worker --app=celery_app.tasks -l info
def test_candles_get_data():
    param_set = [{"from": "2019-10-21T22:00:00.000000000Z",
                  "to": "2019-10-22T22:00:00.000000000Z",
                  "granularity": "H1",
                  "price": "M"},
                 {"from": "2019-10-22T22:00:00.000000000Z",
                  "to": "2019-10-23T22:00:00.000000000Z",
                  "granularity": "H1",
                  "price": "M"},
                 {"from": "2019-10-23T22:00:00.000000000Z",
                  "to": "2019-10-24T04:00:00.000000000Z",
                  "granularity": "H1",
                  "price": "M"}]
    header = [tasks.session_get_data.signature(
        ("AUD_JPY",), {"params": params, "timeout": 30}) for params in param_set]
    callback = tasks.merge_data.s()
    res = chord(header)(callback)
    assert res.get() == None
    with pd.HDFStore("data/AUD_JPY.h5") as store:
        df = store["H1/M"]
    df.sort_index(inplace=True)
    assert df.index[0] == pd.Timestamp("2019-10-21 22:00:00")
    assert df.index[-1] == pd.Timestamp("2019-10-24 03:00:00")
