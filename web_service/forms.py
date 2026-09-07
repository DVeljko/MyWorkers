from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired(), Length(min=8, max=40)])
    submit = SubmitField("Submit")

class AddEmployee(FlaskForm):
    first_name = StringField("Enter a name: ", validators=[DataRequired()])
    last_name = StringField("Enter a last name: ", validators=[DataRequired()])
    email = EmailField("Enter an email: ", validators=[DataRequired(), Email()])
    phone = StringField("Enter a phone number: ", validators=[DataRequired()])
    position = StringField("Enter a position: ", validators=[DataRequired()])
    hire_date = DateField("Hire date: ", validators=[DataRequired()])
    salary = FloatField("Enter a salary: ", validators=[DataRequired()])
    status = StringField("Enter a status: ", validators=[DataRequired()])
    department_id = IntegerField("Enter a department id: ", validators=[DataRequired()])
    submit = SubmitField("Add employee")