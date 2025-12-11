from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length,Email, EqualTo, ValidationError
from firstblog.models import User
from flask_login import current_user
from flask_bcrypt import bcrypt



class RegistrationForm(FlaskForm):
    Username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators =[DataRequired(), Length(min=5,max=8)] )
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('E-mail already registered!! Go Login to the Friends Corner')

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators =[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in')

class UpdateAccountForm(FlaskForm):
    Username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png'])])
    email = StringField('Email',validators=[DataRequired(),Email()])
    submit = SubmitField('Update')


    def validate_username(self, Username):
        if Username.data!=current_user.username:
            user = User.query.filter_by(username=Username.data).first()
            if user:
                raise ValidationError('Username already exists')
    
    def validate_email(self, email):
        if email.data!=current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Username already exists')
    
class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, max=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

    def validate_password(self, password):
        if current_user.is_authenticated and bcrypt.check_password_hash(current_user.password, password.data):
            raise ValidationError('New password must be different from the old password.')