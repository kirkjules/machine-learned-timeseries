from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    SelectMultipleField, SelectField, DateTimeField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')


class CandlesForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    price = SelectMultipleField(
        'Price', validators=[DataRequired()], choices=[
            ("M", "Mid"), ("A", "Ask"), ("B", "Bid")],
        render_kw={"class_": "chosen-select"})
    from_ = DateTimeField('From', validators=[DataRequired()])
    to = DateTimeField('To', validators=[DataRequired()])
    granularity = SelectMultipleField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15", "M15"), ("H1", "H1"), ("H4", "H4")],
        render_kw={"class_": "chosen-select"})
    smooth = BooleanField('Smooth')
    submit = SubmitField('Submit')


class IndicateForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    granularity = SelectField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15", "M15"), ("H1", "H1"), ("H4", "H4")])
    submit = SubmitField('Submit')
