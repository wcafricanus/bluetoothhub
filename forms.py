from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Email, DataRequired, Length


class SignupForm(FlaskForm):
    submit = SubmitField("Sign In")

    email = StringField('Email address', validators=[
        DataRequired('Please provide a valid email address'),
        Length(min=6, message=(u'Email address too short')),
        Email(message=(u'That\'s not a valid email address.'))])
    password = PasswordField('Pick a secure password', validators=[
        DataRequired(),
        Length(min=6, message=(u'Please give a longer password'))])
    display_name = StringField('Choose your username', validators=[DataRequired()])


class LoginForm(FlaskForm):
    submit = SubmitField("Log In")

    email = StringField('Email address', validators=[
        DataRequired('Please provide a valid email address'),
        Length(min=6, message=(u'Email address too short')),
        Email(message=(u'That\'s not a valid email address.'))])
    password = PasswordField('Pick a secure password', validators=[
        DataRequired(),
        Length(min=6, message=(u'Please give a longer password'))])
