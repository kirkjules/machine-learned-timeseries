from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, Optional


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
            ("M15", "M15"), ("H1", "H1"), ("H4", "H4")],
        render_kw={"class_": "chosen-select"})
    system = SelectMultipleField(
        'System', validators=[Optional()], choices=[
            ('close_sma_3 close_sma_5', 'testing close_sma_3, close_sma_5'),
            ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
            ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')],
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
            self.system.data = ['1', '2', '3', '4', '5', '6', '7', '8', '9',
                                '10']
            return True
        else:
            return True
