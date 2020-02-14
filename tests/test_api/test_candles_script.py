# import os
import pytest
import datetime
from uuid import uuid4
from pprint import pprint


def print_db_url():
    """Function to confirm database url is read at function run time."""
    from htp.aux import database
    return str(database.engine.url)


def test_db_url(db):
    """Test that confirm the test fixture database url is set as an environment
    variable prior to the target function being invoked, allowing the function
    to read the desired url."""
    assert print_db_url() == db


def get():
    """Function calling celery tasks to be mocked in the ensuing test."""
    from htp.aux import tasks
    # print(tasks.db_session.bind.engine.url)
    g = tasks.session_get_data.signature(
        ('AUD_JPY',), {'params': {'count': 5}, 'timeout': 30})
    return (g.freeze(), g.id)


def test_mocking_get_(db, mocker):
    """Test to confirm the correct assignment of mock return values to a
    target function along with it's methods and attributes."""
    instance = mocker.patch('htp.aux.tasks.session_get_data.signature')
    instance.return_value.freeze.return_value = '5678'
    instance.return_value.id = '9101'
    assert get() == ('5678', '9101')


@pytest.mark.parametrize(
    'from_',
    [datetime.datetime(2019, 6, 1), datetime.datetime(2019, 8, 17)])
@pytest.mark.parametrize('to', [datetime.datetime(2019, 7, 5)])
def test_arg_prep(db, from_, to):
    """Test to assert basic output characteristics from argument generator."""
    from htp.api.scripts import candles
    param_set = candles.arg_prep({
        'price': 'M', 'granularity': 'M15', 'from': from_, 'to': to,
        'smooth': True})
    pprint(param_set)
    assert isinstance(param_set, list)


def query_func():
    """Function that inserts and queries records from the db, using the session
    defined in the core database module."""
    from htp.aux.database import db_session
    from htp.aux.models import GetTickerTask
    get_id = uuid4()
    db_session.add(GetTickerTask(
        id=get_id, ticker='AUD_JPY', price='M', granularity='M15'))
    db_session.commit()
    entry = db_session.query(GetTickerTask).get(get_id)
    return entry.ticker


def test_query_func(dbsession, mocker):
    """Test to successfully mock the session used in the test function with the
    fixture session defined for testing, ensuring that the tested function's
    logic can be applied to the in memory db."""
    mocker.patch('htp.aux.database.db_session', new_callable=dbsession)
    assert query_func() == 'AUD_JPY'


@pytest.fixture
def candle_get_data(dbsession, mocker):
    """Test to confirm successful task calling and writing to db in wrapping
    function."""
    from htp.api.scripts import candles
    instance = {}
    mocker.patch('htp.api.scripts.candles.db_session', new_callable=dbsession)
    instance['param'] = mocker.patch(
        'htp.aux.tasks.session_get_data.signature')
    instance['param'].return_value.freeze.return_value = None
    instance['callback'] = mocker.patch(
        'htp.aux.tasks.merge_data.s', return_value=1)
    instance['chord'] = mocker.patch(
        'htp.api.scripts.candles.chord', autospec=True)
    candles.get_data('AUD_JPY', ['M'], ['M15'], datetime.datetime(2019, 6, 1),
                     datetime.datetime(2019, 7, 5), True)
    return instance


def test_get_data(candle_get_data):
    print(candle_get_data['param'].call_count)
    assert candle_get_data['callback'].called
    assert candle_get_data['chord'].called
