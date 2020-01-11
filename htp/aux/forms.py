from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, Optional

periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
           35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
systems = [(f"close_sma_{i} close_sma_{j}", f"close_sma_{i} close_sma_{j}")
           for i in periods for j in periods if i < (j - 1)]


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
    granularity = SelectMultipleField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15", "M15"), ("H1", "H1"), ("H4", "H4")],
        render_kw={"class_": "chosen-select"})
    submit = SubmitField('Submit')


class SignalForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired()])
    granularity = SelectMultipleField(
        'Granularity', validators=[DataRequired()], choices=[
            ("M15 H1", "M15"), ("H1 H4", "H1"), ("H4 None", "H4")],
        render_kw={"class_": "chosen-select"})
    system = SelectMultipleField(
        'System', validators=[Optional()], choices=systems,
        render_kw={"class_": "chosen-select"})
    select_all = BooleanField(validators=[Optional()])
    submit = SubmitField('Submit')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        elif not self.select_all.data and not self.system.data:
            self.system.errors.append("Must select at least one system or \
tick select all.")
            return False
        elif self.select_all.data:
            self.system.data = [s[1] for s in systems]
            return True
        else:
            return True
