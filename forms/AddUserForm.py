from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
from wtforms.fields.html5 import EmailField


class AddUserForm(FlaskForm):
    name = StringField('Name', [validators.DataRequired("Please enter your name.")])
    surname = StringField('Surname', [validators.DataRequired("Please enter your surname.")])
    email = EmailField('Email', [validators.DataRequired("Please enter your email address."),
                                 validators.Email("Please enter a valid email address.")])
    subject = StringField('Subject', [validators.DataRequired('Please enter the subject name.')])
    course_no = StringField('Course #', [validators.DataRequired('Please enter the course number.')])
    course_section = StringField('Section', [validators.DataRequired('Please enter the course section.')])
    submit_button = SubmitField('Submit')