from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class UserInformation(UserMixin, db.Model):
    __tablename__ = "UserInformation"
    id = db.Column('id', db.Integer, primary_key=True, unique=True, index=True)
    username = db.Column('username', db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(200))
    registered_on = db.Column('registered_on', db.DateTime)
    email = db.Column('email', db.String(20))
    admin = db.Column('is_admin', db.Boolean)
    rank = db.Column('rank', db.Integer)
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.admin = False
        self.registered_on = datetime.utcnow()

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.username)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

@login.user_loader
def load_user(id):
    return UserInformation.query.get(int(id))


class UserProblemSubmission(db.Model):
    __tablename__ = "UserProblemSubmission"
    id = db.Column("id", db.Integer, primary_key=True, unique=True, index=True)
    timesubmission = db.Column('submitted_on', db.DateTime)
    timeprocessed = db.Column('processed_on', db.DateTime)
    username = db.Column('user_code', db.String(20), db.ForeignKey('UserInformation.username'))
    problem_code = db.Column('problem_code', db.String(20), db.ForeignKey('ProblemInformation.code'))
    filename = db.Column('filename', db.String(50), unique=True)
    amountpass = db.Column('amount_case_pass', db.Integer)
    amountfail = db.Column('amount_case_fail', db.Integer)
    success = db.Column('is_sucess', db.Boolean)
    processed = db.Column('is_processed', db.Boolean)
    reportjson = db.Column('reportjson', db.String(4096))
    def __init__(self, username, problem_code, filename, amountpass, amountfail, success, reportjson, processed):
        self.username = username
        self.problem_code = problem_code
        self.filename = filename
        self.amountpass = amountpass
        self.amountfail = amountfail
        self.success =  success
        self.reportjson = reportjson
        self.timesubmission = datetime.utcnow()
        self.processed = processed


class Section(db.Model):
    __tablename__ = "Section"
    id = db.Column('id', db.Integer, primary_key=True, index=True)
    timecreated = db.Column('created_on', db.DateTime)
    code = db.Column('code', db.String(20), unique=True, index=True)
    name = db.Column('name', db.String(20))
    description = db.Column('description', db.String(50))
    visible = db.Column('is_visible', db.Boolean)
    def __init__(self, code, name, description):
        self.code = code
        self.name = name
        self.description = description
        self.timecreated = datetime.utcnow()
        self.visible = False


class SectionProblemRelation(db.Model):
    __tablename__ = "SectionProblemRelation"
    id = db.Column('id', db.Integer, primary_key=True, index=True)
    sectioncode = db.Column('section_code', db.String(20), db.ForeignKey('Section.code'))
    problemcode = db.Column('problem_code', db.String(20), db.ForeignKey('ProblemInformation.code'))
    def __init__(self, sectioncode, problemcode):
        self.sectioncode = sectioncode
        self.problemcode = problemcode


class ProblemInformation(db.Model):
    __tablename__ = "ProblemInformation"
    id = db.Column('id', db.Integer, primary_key=True, index=True)
    code = db.Column('code', db.String(20), unique=True, index=True)
    name = db.Column('name', db.String(20))
    created_on = db.Column('created_on', db.DateTime)
    shortdescription = db.Column('short_description', db.String(50))
    description_file = db.Column('description_file', db.Integer)
    visible = db.Column('is_visible', db.Boolean)
    timelimit = db.Column('timelimit', db.Integer)
    judge_cmd = db.Column('judge_cmd', db.String(128))
    def __init__(self, code, name, shortdescription, timelimit, judge_cmd):
        self.code = code
        self.name = name
        self.shortdescription = shortdescription
        self.visible = False
        self.timelimit = timelimit
        self.judge_cmd = judge_cmd
        self.created_on = datetime.utcnow()


class ProblemFile(db.Model):
    __tablename__ = "ProblemFile"
    id = db.Column('id', db.Integer, primary_key=True, index=True)
    problem_code = db.Column('code', db.String(20), db.ForeignKey('ProblemInformation.code'), index=True)
    file_name = db.Column('name', db.String(32))
    visible = db.Column('is_visible', db.Boolean)
    def __init__(self, problem_code, file_name, visible):
        self.problem_code = problem_code
        self.file_name = file_name
        self.visible = visible


class ProblemTestCaseInformation(db.Model):
    __tablename__ = "ProblemTestCaseInformation"
    id = db.Column('id', db.Integer, primary_key=True, index=True)
    problem_code = db.Column('code', db.String(20), db.ForeignKey('ProblemInformation.code'), index=True)
    test_case = db.Column('testcase', db.Integer)
    input_file = db.Column('input_file', db.Integer, db.ForeignKey('ProblemFile.id'))
    res_file = db.Column('res_file', db.Integer, db.ForeignKey('ProblemFile.id'))
    is_open_case = db.Column('is_open_case', db.Boolean)
    def __init__(self, problem_code, test_case, input_file, res_file, is_open):
        self.problem_code = problem_code
        self.test_case = test_case
        self.input_file = input_file
        self.res_file = res_file
        self.is_open_case = is_open


