from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional, length
from app.models import UserInformation, Section, ProblemInformation, ProblemFile
from flask_login import current_user
from werkzeug.security import check_password_hash
import config

import os


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = UserInformation.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = UserInformation.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ChangePasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    current = PasswordField('Current password', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if not(current_user.admin or current_user.username == username):
            raise ValidationError('It must be your username')
        if UserInformation.query.filter_by(username=username.data).first() is None:
            raise ValidationError('It must be your username')                

    def validate_current(self, current):
        if not check_password_hash(current_user.password, current.data):
            raise ValidationError('Incorrect password')


class AdminSectionForm(FlaskForm):
    code = StringField('Code', validators=[Optional(), length(max=20)])
    name = StringField('Name', validators=[DataRequired(), length(max=20)])
    description = StringField('Short description', validators=[DataRequired(), length(max=50)])
    visible = BooleanField('Should it be visible?')
    delete = BooleanField('Delete?')
    submit = SubmitField('Add/Update!')

    def validate_code(self, code):
        if code.data == 'new':
            raise ValidationError('Code must not be new')


class AdminProblemForm(FlaskForm):
    code = StringField('Code', validators=[Optional(), length(max=20)])
    name = StringField('Name', validators=[DataRequired(), length(max=20)])
    shortdescription = StringField('Short description', validators=[DataRequired(), length(max=50)])
    description = TextAreaField('Description', validators=[DataRequired(), length(max=32768)])
    judge_cmd = StringField('Judge command', validators=[DataRequired(), length(max=128)])
    timelimit = IntegerField('Timelimit', validators=[DataRequired()])
    visible = BooleanField('Should it be visible?')
    delete = BooleanField('Delete?')
    submit = SubmitField('Add/Update!')

    def validate_code(self, code):
        if code.data == 'new':
            raise ValidationError('Code must not be new')


class SectionProblemConnectForm(FlaskForm):
    sectioncode = StringField('Section Code', validators=[DataRequired(), length(max=20)])
    problemcode = StringField('Problem Code', validators=[DataRequired(), length(max=20)])
    delete = BooleanField('Delete?')
    submit = SubmitField('Add/Update!')

    def validate_sectioncode(self, sectioncode):
        if Section.query.filter_by(code=sectioncode.data).first() is None:
            raise ValidationError('Please insert a valid section')

    def validate_problemcode(self, problemcode):
        if ProblemInformation.query.filter_by(code=problemcode.data).first() is None:
            raise ValidationError('Please insert a valid problem')


class UploadFileForm(FlaskForm):
    file_name = StringField('File name', validators=[DataRequired(), length(max=32)])
    file_sent = FileField('File', validators=[DataRequired()])
    visible = BooleanField('Should it be visible?')
    submit = SubmitField('Upload file')


class DeleteFileForm(FlaskForm):
    file_id = IntegerField('File id', validators=[DataRequired()])
    submit = SubmitField('Delete file')

    def validate_file_id(self, file_id):
        if not ProblemFile.query.filter_by(id=file_id.data).first():
            raise ValidationError('This file id does not exist')


class SetTestCaseForm(FlaskForm):
    test_case = IntegerField('Test case', validators=[DataRequired()])
    input_file = IntegerField('Input file', validators=[DataRequired()])
    res_file = IntegerField('Response file', validators=[DataRequired()])
    is_open = BooleanField('Is it an open case?')
    submit = SubmitField('Set test case')
    
    def validate_input_file(self, input_file):
        if not ProblemFile.query.filter_by(id=input_file.data).first():
            raise ValidationError('This file id does not exist')

    def validate_res_file(self, res_file):
        if not ProblemFile.query.filter_by(id=res_file.data).first():
            raise ValidationError('This file id does not exist')

class DeleteTestCaseForm(FlaskForm):
    test_case = IntegerField('Test case', validators=[DataRequired()])
    submit = SubmitField('Delete test case relation')



