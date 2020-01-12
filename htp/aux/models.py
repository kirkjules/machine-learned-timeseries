from htp import login
from htp.aux.database import Base
from flask_login import UserMixin
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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


class genSignalTask(Base):
    __tablename__ = 'genSignalTask'
    id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("getTickerTask.id"))
    sma_close_x = Column(String(15))
    sma_close_y = Column(String(15))
    trade_direction = Column(String(4))
    exit_strategy = Column(String(20))
    status = Column(Integer)
    signal_count = Column(Integer)
    batch_number = Column(Integer)
