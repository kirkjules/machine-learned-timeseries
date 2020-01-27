from htp import login
from htp.aux.database import Base
from flask_login import UserMixin
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(128))

    def __init__(self, username=None, password_hash=None):
        self.username = username
        self.password_hash = password_hash

    def __repr__(self):
        return '<User %r>' % (self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class getTickerTask(Base):
    __tablename__ = 'getTickerTask'
    id = Column(
        UUID(as_uuid=True), primary_key=True, unique=True)
    ticker = Column(String(50))
    price = Column(String(1))
    granularity = Column(String(3))
    status = Column(Integer)
    _from = Column(DateTime())
    to = Column(DateTime())
    get_subtasks = relationship("subTickerTask", backref="getTickerTask")
    indicator_tasks = relationship(
        "indicatorTask", backref=backref("getTickerTask", uselist=False))


class candles(Base):
    __tablename__ = 'candles'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    open = Column(Float(precision=6))
    high = Column(Float(precision=6))
    low = Column(Float(precision=6))
    close = Column(Float(precision=6))


class subTickerTask(Base):
    __tablename__ = 'subTickerTask'
    id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    get_id = Column(UUID(as_uuid=True), ForeignKey("getTickerTask.id"))
    _from = Column(DateTime(), nullable=False)
    to = Column(DateTime(), nullable=False)
    status = Column(Integer)
    error = Column(String(120))


class indicatorTask(Base):
    __tablename__ = 'indicatorTask'
    get_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), primary_key=True,
        unique=True)
    adx_status = Column(Integer)
    atr_status = Column(Integer)
    stochastic_status = Column(Integer)
    rsi_status = Column(Integer)
    macd_status = Column(Integer)
    ichimoku_status = Column(Integer)
    sma_status = Column(Integer)
    status = Column(Integer)


class ichimokukinkohyo(Base):
    __tablename__ = 'ichimokukinkohyo'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    tenkan = Column(Float(precision=6))
    kijun = Column(Float(precision=6))
    chikou = Column(Float(precision=6))
    senkou_A = Column(Float(precision=6))
    senkou_B = Column(Float(precision=6))


class stochastic(Base):
    __tablename__ = 'stochastic'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    percK = Column(Float(precision=6))
    percD = Column(Float(precision=6))


class relativestrengthindex(Base):
    __tablename__ = 'relativestrengthindex'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    avg_gain = Column(Float(precision=6))
    avg_loss = Column(Float(precision=6))
    rs = Column(Float(precision=6))
    rsi = Column(Float(precision=6))


class momentum(Base):
    __tablename__ = 'momentum'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    atr = Column(Float(precision=6))
    adx = Column(Float(precision=6))


class movavgconvdiv(Base):
    __tablename__ = 'movavgconvdiv'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    timestamp = Column(DateTime())
    emaF = Column(Float(precision=6))
    emaS = Column(Float(precision=6))
    macd = Column(Float(precision=6))
    signal = Column(Float(precision=6))
    histogram = Column(Float(precision=6))


class smoothmovingaverage(Base):
    __tablename__ = 'smoothmovingaverage'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
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


class genSignalTask(Base):
    __tablename__ = 'genSignalTask'
    id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("getTickerTask.id"))
    fast = Column(String(15))
    slow = Column(String(15))
    trade_direction = Column(String(4))
    exit_strategy = Column(String(20))
    status = Column(Integer)
    signal_count = Column(Integer)
    batch_number = Column(Integer)


class signals(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("genSignalTask.id"), unique=False)
    get_id = Column(
        UUID(as_uuid=True), ForeignKey("getTickerTask.id"), unique=False)
    entry_datetime = Column(DateTime())
    entry_price = Column(Float(precision=6))
    stop_loss = Column(Float(precision=6))
    exit_datetime = Column(DateTime())
    exit_price = Column(Float(precision=6))
