from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db, queue
from app.forms import LoginForm, RegistrationForm
from app.models import UserInformation
from app import sections, problems

from rq.job import Job
from worker.worker import conn


@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home', sections=sections.section.values())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UserInformation.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    return render_template("register_disabled.html")
    """Register Form"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = UserInformation(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    

@app.route("/logout")
def logout():
    """Logout Form"""
    logout_user()
    return redirect(url_for('index'))


@app.route('/section/<section_id>')
@login_required
def section(section_id):
    """Display a specific section"""
    if section_id in sections.section:
        sect = sections.section[section_id]
        if sect.visible:
            return render_template('section.html', title='Section', problems=sect.problems)
    return redirect(url_for('index'))


def process_submission(id):
    #execute for submission id
    userid = 0
    problemid = 0
    amountpass = 0
    amountfail = 0
    success = False
    reportjson = ''

    #save the results
    try:
        results = UserProblemSubmission(userid, problemid, amountpass, amountfail, success, reportjson)
        db.session.add(result)
        db.session.commit()
        return results.id
    except Exception as e:
        print(e)


@app.route('/problem/<problem_id>', methods = ['GET' , 'POST'])
@login_required
def problem(problem_id):
    """Display a specific section"""
    if request.method == "POST":
        job = queue.enqueue_call(func = process_submission, args=("",), result_ttl=5000)
        print(job.get_id())
    if problem_id in problems:
        prob = problems[problem_id]
        return render_template('problem.html', title='Problem', problem=prob)
    return redirect(url_for('index'))


@app.route('/get_file/<problem_id>/<file>')
@login_required
def get_file(problem_id, file):
    return "{}: {}".format(problem_id, file)


@app.route('/results/<job_key>', methods=['GET'])
@login_required
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)
    if job.is_finished:
        return str(job.result), 200
    else:
        return "Nay!", 202



