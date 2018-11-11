from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class UserInformation(UserMixin, db.Model):
    __tablename__ = "UserInformation"
    id = db.Column('user_id', db.Integer, primary_key=True, unique=True, index=True)
    username = db.Column('username', db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(200), unique=True)
    salt = db.Column('salt', db.String(40))
    registered_on = db.Column('registered_on' , db.DateTime)
    email = db.Column('email', db.String(20))
    admin = db.Column('is_admin', db.Boolean)
    rank = db.Column('rank', db.Integer)

    def __init__(self, username, email):
        self.username = username
        self.email = email
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
    id = db.Column("submission_id", db.Integer, primary_key=True, unique=True, index=True)
    timesubmission = db.Column('submitted_on', db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('UserInformation.username'))
    problemid = db.Column('problem_id', db.Integer)
    amountpass = db.Column('amount_case_pass', db.Integer)
    amountfail = db.Column('amount_case_fail', db.Integer)
    success = db.Column('is_sucess', db.Boolean)
    reportjson = db.Column('reportjson', db.String(4096))

    def __init__(self, userid, problemid, amountpass, amountfail, success, reportjson):
        self.userid = userid
        self.problemid = problemid
        self.amountpass = amountpass
        self.amountfail = amountfail
        self.success =  success
        self.reportjson = reportjson
        self.timesubmission = datetime.utcnow()


"""
class ProblemGroup(db.Model):
    __tablename__ = "ProblemGroup"
    id = db.Column('problem_group_id', db.Integer, primary_key=True)
    timecreated = db.Column('created_on', db.DateTime)
    name = db.Column('name', db.String(20))
    description = db.Column('description', db.String(50))
    visible = db.Column('is_visible', db.Boolean)


class ProblemInfo(db.Model):
    __tablename__ = "ProblemInfo"
    id = db.Column('problem_id', db.Integer, primary_key=True, index=True)
    problemgroup = db.Column(db.Integer, db.ForeignKey('ProblemGroup.problem_group_id'), index=True)
    created_on = db.Column('created_on', db.DateTime)
    shortdescription = db.Column('description', db.String(50))
    link = db.Column('link', db.String(50))
    visible = db.Column('is_visible', db.Boolean)
    amount_pass = db.Column('amount_pass', db.Integer)
    amount_fail = db.Column('amount_fail', db.Integer)
    rulesjson = db.Column('rulesjson', db.String(32768)) #(each input file, timelimit, other related files for download)
"""
