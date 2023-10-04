from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Email, Length, Optional
from models import User, bcrypt
from flask import g


    
class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken. Please choose a different username.')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class UserProfileForm(FlaskForm):
    """Form for editing user profile."""

    username = StringField('Username', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    bio = TextAreaField('Bio', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional()])
    header_image_url = StringField('Header Image URL', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    password = PasswordField('Password', validators=[Length(min=6), DataRequired()])

    def validate_password(self, field):
        # Check if the entered password matches the user's current password
        user = User.query.get_or_404(g.user.id)  # Assuming g.user is the current user
        if not bcrypt.check_password_hash(user.password, field.data):
            raise ValidationError('Incorrect password')

