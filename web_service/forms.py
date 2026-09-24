from flask_wtf import FlaskForm

from wtforms import (
    EmailField,
    PasswordField,
    SubmitField,
    StringField,
    IntegerField,
    FloatField,
    DateField,
    SelectField
)

from wtforms.validators import DataRequired, Length, Email


class LoginForm(FlaskForm):

    email = EmailField(
        "Email:",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password:",
        validators=[DataRequired(), Length(min=8, max=40)]
    )

    submit = SubmitField("Submit")


class AddEmployee(FlaskForm):

    first_name = StringField(
        "Enter a name:",
        validators=[DataRequired()]
    )

    last_name = StringField(
        "Enter a last name:",
        validators=[DataRequired()]
    )

    email = EmailField(
        "Enter an email:",
        validators=[DataRequired(), Email()]
    )

    phone = StringField(
        "Enter a phone number:",
        validators=[DataRequired()]
    )

    position = StringField(
        "Enter a position:",
        validators=[DataRequired()]
    )

    hire_date = DateField(
        "Hire date:",
        validators=[DataRequired()]
    )

    salary = FloatField(
        "Enter a salary:",
        validators=[DataRequired()]
    )

    status = SelectField(
        "Status:",
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive")
        ],
        validators=[DataRequired()]
    )

    department_id = SelectField(
        "Department:",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Add employee")


class AcceptEmployeeForm(FlaskForm):

    phone = StringField(
        "Phone number:",
        validators=[DataRequired()]
    )

    position = StringField(
        "Position:",
        validators=[DataRequired()]
    )

    hire_date = DateField(
        "Hire date:",
        validators=[DataRequired()]
    )

    salary = FloatField(
        "Salary:",
        validators=[DataRequired()]
    )

    department_id = SelectField(
        "Department:",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Accept Employee")


class AddDepartment(FlaskForm):

    name = StringField(
        "Department name:",
        validators=[DataRequired()]
    )

    submit = SubmitField("Add Department")


class RegisterForm(FlaskForm):

    owner_first_name = StringField(
        "First name",
        validators=[DataRequired()]
    )

    owner_last_name = StringField(
        "Last name",
        validators=[DataRequired()]
    )

    company_name = StringField(
        "Company name",
        validators=[DataRequired()]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Register")


class EmployeeRegisterForm(FlaskForm):

    first_name = StringField(
        "First name",
        validators=[DataRequired()]
    )

    last_name = StringField(
        "Last name",
        validators=[DataRequired()]
    )

    company_id = IntegerField(
        "Company ID",
        validators=[DataRequired()]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Send request")