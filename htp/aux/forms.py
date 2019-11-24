from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class CandlesForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    price = SelectMultipleField(
        'Price', validators=[DataRequired()], choices=[
            ("M", "Mid"), ("A", "Ask"), ("B", "Bid")])
    from_ = DateTimeField('From', validators=[DataRequired()])
    to = DateTimeField('To', validators=[DataRequired()])
    granularity = SelectMultipleField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15", "M15"), ("H", "H"), ("H4", "H4")])
    smooth = BooleanField('Smooth')
    submit = SubmitField('Acquire')


class IndicateForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    price = SelectMultipleField(
        'Price', validators=[DataRequired()], choices=[
            ("M", "Mid"), ("A", "Ask"), ("B", "Bid")])
    granularity = SelectMultipleField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15", "M15"), ("H", "H"), ("H4", "H4")])
    smooth = BooleanField('Smooth')
    submit = SubmitField('Acquire')
