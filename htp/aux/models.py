from htp import login
from htp.aux.database import Base
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime
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


class CandlesTasks(Base):
    __tablename__ = 'candlestasks'
    id = Column(Integer, primary_key=True)  # default set autoincrement=True
    ticker = Column(String(50))
    from_ = Column(DateTime())
    to = Column(DateTime())
    granularity = Column(String(3))
    price = Column(String(1))
    task_id = Column(String(50))
    task_status = Column(String(50))
    task_error = Column(String(120))
