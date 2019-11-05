import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(os.environ['DATABASE'], convert_unicode=True)

# configured factory that creates new Session objects when called
session_factory = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# scoped_session object represents a registry of Session objects
db_session = scoped_session(session_factory)

Base = declarative_base()

# descriptor that returns you a Query based on the class you accessed it from
# e.g. Foo.query is a shorthand for db_session.query(Foo)
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import htp.models
    Base.metadata.create_all(bind=engine)
