import os
import pytest
from htp.api import oanda
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


@pytest.fixture(scope='class')
def db():
    os.environ['DATABASE'] = 'sqlite://'
    return os.getenv('DATABASE')


# fixture functions for db testing
@pytest.fixture(scope='class')
def engine(db):
    """Create a test db that can be used with app functionality."""
    return create_engine(db, echo=False)


@pytest.fixture(scope='class')
def tables(engine):
    """Generate all tables in htp.aux.models in SQLite testing DB."""
    from htp.aux.database import Base, init_db
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


@pytest.fixture
def df():
    """Generate test candle data to use as a standard fixture."""

    def _get(ticker, queryParameters):
        return oanda.Candles.to_df(
            oanda.Candles(instrument=ticker, queryParameters=queryParameters
                          ).r.json(), queryParameters['price'])

    return _get
