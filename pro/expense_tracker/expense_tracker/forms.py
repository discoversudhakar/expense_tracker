from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, StringField, DateField, SubmitField, PasswordField, EmailField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Email, EqualTo, Length, ValidationError
from models import User
from datetime import date

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[
        DataRequired(message='Amount is required'),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ])
    
    category = SelectField('Category', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        from models import Category
        self.category.choices = [(c.name, c.name) for c in Category.query.order_by(Category.name).all()]
    
    description = TextAreaField('Description', validators=[
        Length(max=200, message='Description must be less than 200 characters')
    ])
    
    date = DateField('Date', validators=[DataRequired()], default=date.today)

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)],
                           description='Leave blank to keep current password')
    password2 = PasswordField('Repeat Password', validators=[EqualTo('password')])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('admin', 'Admin')], default='customer')
    submit = SubmitField('Save User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
