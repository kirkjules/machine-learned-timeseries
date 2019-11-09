from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class CandlesForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    from_ = StringField('From', validators=[DataRequired()])
    to = StringField('To', validators=[DataRequired()])
    granularity = StringField('Granularity', validators=[DataRequired()])
    smooth = BooleanField('Smooth')
    submit = SubmitField('Acquire')
