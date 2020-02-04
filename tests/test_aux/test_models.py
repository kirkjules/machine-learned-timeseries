import pytest
import numpy as np
import pandas as pd
from uuid import uuid4
# from htp.api import oanda
from datetime import datetime as d
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from htp.aux.database import Base, init_db
from htp.aux.models import User, GetTickerTask, SubTickerTask, Candles


# fixture functions for db testing
@pytest.fixture(scope='class')
def engine():
    """Create a test db that can be used with app functionality."""
    return create_engine('sqlite://', echo=False)


@pytest.fixture(scope='class')
def tables(engine):
    """Generate all tables in htp.aux.models in SQLite testing DB."""
    init_db(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='class')
def dbsession(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down
    everything properly."""
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    yield session

    session.remove()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


def test_get_task_sub_task_relationship():  # dbsession):
    """Test the db relationship between the get_ticker and sub_get_ticker
    tables"""
    g = GetTickerTask()
    s = SubTickerTask()
    assert len(g.sub_tasks) == 0
    assert s.get_ticker is None


def test_user_creation(dbsession):
    """Test user creation and password saving functionality."""
    new_user = User(username='newuser')
    new_user.set_password('password1')
    dbsession.add(new_user)
    old_user = dbsession.query(User).filter(User.username == 'newuser').first()
    assert old_user.check_password('password1')


def test_task_to_data_relationship(dbsession):
    """Test data integrity across relationship between tables."""
    get_id = uuid4()
    g = GetTickerTask(
        id=get_id, ticker='AUD_JPY', price='M', granularity='M15',
        _from=d.strptime('2018-02-01 13:00:00', '%Y-%m-%d %H:%M:%S'),
        to=d.strptime('2018-04-30 13:00:00', '%Y-%m-%d %H:%M:%S'))
    s = [SubTickerTask(get_id=get_id, _from=d.strptime(
                           '2018-02-01 13:00:00', '%Y-%m-%d %H:%M:%S'),
                       to=d.strptime(
                           '2018-03-01 12:45:00', '%Y-%m-%d %H:%M:%S')),
         SubTickerTask(get_id=get_id, _from=d.strptime(
                           '2018-03-01 13:00:00', '%Y-%m-%d %H:%M:%S'),
                       to=d.strptime(
                           '2018-04-01 12:45:00', '%Y-%m-%d %H:%M:%S')),
         SubTickerTask(get_id=get_id, _from=d.strptime(
                           '2018-04-01 13:00:00', '%Y-%m-%d %H:%M:%S'),
                       to=d.strptime(
                           '2018-04-30 13:00:00', '%Y-%m-%d %H:%M:%S'))]
    entries = [g] + s
    dbsession.add_all(entries)
    assert len(dbsession.query(GetTickerTask).get(get_id).sub_tasks) == 3


@pytest.fixture
def save_to_table(df, dbsession):
    """Generate and save data to candles table."""
    get_id = uuid4()
    g = GetTickerTask(
        id=get_id, ticker='AUD_JPY', price='M', granularity='H1',
        _from=d.strptime('2018-02-01 13:00:00', '%Y-%m-%d %H:%M:%S'),
        to=d.strptime('2018-03-01 13:00:00', '%Y-%m-%d %H:%M:%S'))
    dbsession.add(g)

    data = df('AUD_JPY',
              {'from': '2018-02-01T13:00:00.000000000Z', 'smooth': True,
               'to': '2018-03-01T13:00:00.000000000Z', 'granularity': 'H1',
               'price': 'M'})
    data['batch_id'] = get_id
    data.reset_index(inplace=True)
    data.rename(columns={'index': 'timestamp'}, inplace=True)
    rows = data.to_dict('records')

    # conversion to datetime object only required for SQLite backend.
    for entry in rows:
        entry['timestamp'] = entry['timestamp'].to_pydatetime()

    dbsession.bulk_insert_mappings(Candles, rows)
    return (get_id, data)


def test_ticker_data_save_to_table(save_to_table, dbsession):
    """Test candle data being saved and extracted from table, ensuring data
    is unchanged by operations."""
    assert len(
        dbsession.query(GetTickerTask).get(save_to_table[0]).candle_data) ==\
        len(save_to_table[1].index)


def test_data_integrity(save_to_table, dbsession):
    dt = []
    open = []
    high = []
    low = []
    close = []
    for row in dbsession.query(Candles).all():
        dt.append(row.timestamp)
        open.append(row.open)
        high.append(row.high)
        low.append(row.low)
        close.append(row.close)

    np_data = np.stack((dt, open, high, low, close), axis=-1)
    df_data = pd.DataFrame(
        np_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
    df_og = save_to_table[1].drop('batch_id', axis=1).copy()
    pd.testing.assert_frame_equal(df_og, df_data)
