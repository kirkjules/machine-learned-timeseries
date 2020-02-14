import uuid
from htp import login
from htp.aux.database import Base
from flask_login import UserMixin
from sqlalchemy.orm import relationship  # , backref
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float,\
        Boolean, ForeignKeyConstraint
from werkzeug.security import generate_password_hash, check_password_hash


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class User(Base, UserMixin):
    """Table to store user's username and encrypted password."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(128))

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % (self.username)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class GetTickerTask(Base):
    """Table to store ticker data query arguments."""
    __tablename__ = 'get_ticker'
    id = Column(GUID, primary_key=True, unique=True)
    ticker = Column(String(50))
    price = Column(String(1))
    granularity = Column(String(3))
    status = Column(Integer)
    _from = Column(DateTime())
    to = Column(DateTime())
    sub_tasks = relationship('SubTickerTask', backref='get_ticker')
    candle_data = relationship('Candles', backref='get_ticker')
    indicator_tasks = relationship('IndicatorTask', backref='get_ticker')


class SubTickerTask(Base):
    """Table to store sub query data arguments."""
    __tablename__ = 'sub_get_ticker'
    # id = Column(GUID, primary_key=True, unique=True)
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(GUID, ForeignKey("get_ticker.id"), unique=False)
    _from = Column(DateTime(), nullable=False)
    to = Column(DateTime(), nullable=False)
    status = Column(Integer)
    error = Column(String(120))


class Candles(Base):
    """Table to store instrument timeseries data."""
    __tablename__ = 'candles'
    # id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        GUID, ForeignKey("get_ticker.id"), primary_key=True, unique=False)
    timestamp = Column(DateTime(), primary_key=True, unique=False)
    open = Column(String(10))
    high = Column(String(10))
    low = Column(String(10))
    close = Column(String(10))
    indicators = relationship(
        'Indicators', uselist=False, back_populates='candles')


class IndicatorTask(Base):
    __tablename__ = 'indicator_task'
    batch_id = Column(
        GUID, ForeignKey("get_ticker.id"), primary_key=True, unique=True)
    momentum = Column(Boolean())
    stochastic = Column(Boolean())
    relative_strength = Column(Boolean())
    convergence_divergence = Column(Boolean())
    ichimoku = Column(Boolean())
    moving_average = Column(Boolean())
    status = Column(Boolean())


class Indicators(Base):
    __tablename__ = 'indicators'
    __table_args__ = (ForeignKeyConstraint(
        ['batch_id', 'timestamp'], ['candles.batch_id', 'candles.timestamp']),)
    batch_id = Column(GUID, primary_key=True, unique=False)
    timestamp = Column(DateTime(), primary_key=True, unique=False)
    tenkan = Column(String(20))
    kijun = Column(String(20))
    chikou = Column(String(20))
    senkou_A = Column(String(20))
    senkou_B = Column(String(20))
    percK = Column(String(20))
    percD = Column(String(20))
    rsi = Column(String(20))
    atr = Column(String(20))
    adx = Column(String(20))
    macd = Column(String(20))
    signal = Column(String(20))
    histogram = Column(String(20))
    candles = relationship(
        'Candles', uselist=False, back_populates='indicators')


class moving_average(Base):
    __tablename__ = 'moving_average'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(GUID, ForeignKey("get_ticker.id"), unique=False)
    timestamp = Column(DateTime())
    close_sma_3 = Column(Float(precision=6))
    close_sma_4 = Column(Float(precision=6))
    close_sma_5 = Column(Float(precision=6))
    close_sma_6 = Column(Float(precision=6))
    close_sma_7 = Column(Float(precision=6))
    close_sma_8 = Column(Float(precision=6))
    close_sma_9 = Column(Float(precision=6))
    close_sma_10 = Column(Float(precision=6))
    close_sma_12 = Column(Float(precision=6))
    close_sma_14 = Column(Float(precision=6))
    close_sma_15 = Column(Float(precision=6))
    close_sma_16 = Column(Float(precision=6))
    close_sma_20 = Column(Float(precision=6))
    close_sma_24 = Column(Float(precision=6))
    close_sma_25 = Column(Float(precision=6))
    close_sma_28 = Column(Float(precision=6))
    close_sma_30 = Column(Float(precision=6))
    close_sma_32 = Column(Float(precision=6))
    close_sma_35 = Column(Float(precision=6))
    close_sma_36 = Column(Float(precision=6))
    close_sma_40 = Column(Float(precision=6))
    close_sma_48 = Column(Float(precision=6))
    close_sma_50 = Column(Float(precision=6))
    close_sma_60 = Column(Float(precision=6))
    close_sma_64 = Column(Float(precision=6))
    close_sma_70 = Column(Float(precision=6))
    close_sma_72 = Column(Float(precision=6))
    close_sma_80 = Column(Float(precision=6))
    close_sma_90 = Column(Float(precision=6))
    close_sma_96 = Column(Float(precision=6))
    close_sma_100 = Column(Float(precision=6))


class GenSignalTask(Base):
    __tablename__ = 'generate_signals'
    id = Column(GUID, primary_key=True, unique=True)
    batch_id = Column(GUID, ForeignKey("get_ticker.id"))
    fast = Column(String(15))
    slow = Column(String(15))
    trade_direction = Column(String(4))
    exit_strategy = Column(String(20))
    status = Column(Integer)
    signal_count = Column(Integer)
    batch_number = Column(Integer)


class Signals(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(GUID, ForeignKey("generate_signals.id"), unique=False)
    entry_datetime = Column(DateTime())
    entry_price = Column(Float(precision=6))
    stop_loss = Column(Float(precision=6))
    exit_datetime = Column(DateTime())
    exit_price = Column(Float(precision=6))
    conv_entry_price = Column(Float(precision=6))
    conv_exit_price = Column(Float(precision=6))
    close_in_atr = Column(Integer)
    close_to_fast_by_atr = Column(Float(precision=6))
    close_to_slow_by_atr = Column(Float(precision=6))


class Results(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(GUID, ForeignKey("generate_signals.id"), unique=False)
    entry_datetime = Column(DateTime())
    exit_datetime = Column(DateTime())
    PL_PIPS = Column(Float(precision=2))
    POS_SIZE = Column(Integer)
    PL_AUD = Column(Float(precision=2))
    PL_REALISED = Column(Float(precision=2))
