from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from web_app import database, models, create_app, login
import pytest
import os


# incremental marker which is to be used on classes
def pytest_configure(config):
    config.addinivalue_line("markers", "incremental: for step testing.")

def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item

def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed ({})".format(previousfailed.name))


# fixture functions for db testing
@pytest.fixture(scope='class')
def engine():
    """Create a test db that can be used with app functionality."""
    return create_engine(
        'sqlite:////Users/juleskirk/Documents/tutorials/instance/test.db',
        echo=True)


@pytest.fixture(scope='class')
def tables(engine):
    database.Base.metadata.create_all(engine)
    yield
    database.Base.metadata.drop_all(engine)


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


# fixture function for flask app testing
@pytest.fixture()
def client():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client
