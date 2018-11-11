from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, db, queue
from app.forms import LoginForm, RegistrationForm
from app.models import UserInformation, UserProblemSubmission

from app import sections, problems

from rq.job import Job
from worker import conn

import os
from subprocess import Popen, TimeoutExpired
import resource

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


def process_submission(problem_id, username, filename, ):
    #execute for submission id
    amountpass = 0
    amountfail = 0
    reportjson = dict()

    def exec(case, input, res, timelimit, in_and_out = False):
        original_wd = os.getcwd()
        script_file = os.getcwd() + '/' + app.config['UPLOAD_FOLDER'] + '/' + filename
        tempfile = os.getcwd() + '/' + app.config['TEMPORARY_FOLDER'] + '/' + filename + '.out'
        os.chdir(app.config['PROBLEMS_DIR'] + '/' + problem_id)
        def setlimits():
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        proc = Popen(prob.judge_line.format(input, script_file, tempfile, tempfile, res), shell=True, preexec_fn=setlimits)
        try:
            outs, errs = proc.communicate(timeout=timelimit)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate() 
            if in_and_out:
                reportjson[case] = 'timelimit'
        if in_and_out:
            reportjson[input] = '{};{}'.format(outs, errs)
        os.unlink(tempfile)
        os.chdir(original_wd)
        return False

    prob = problems[problem_id]
    timelimit = prob.timelimit
    for index, i in zip(range(len(prob.open_testcases)), prob.open_testcases):
        input = i['input']
        res = i['output']
        if exec(index, input, res, timelimit, in_and_out=True):
            amountpass = amountpass + 1
        else:
            amountfail = amountfail + 1
        
    for index, i in zip(range(len(prob.closed_testcases)), prob.closed_testcases):
        input = i['input']
        res = i['output']
        if exec(index, input, res, timelimit, in_and_out=False):
            amountpass = amountpass + 1
        else:
            amountfail = amountfail + 1

    if amountfail == 0:
        success = False
    else:
        success = True

    #save the results
    try:
        result = UserProblemSubmission(username, problem_id, amountpass, amountfail, success, str(reportjson))
        db.session.add(result)
        db.session.commit()
        return result.id
    except Exception as e:
        print(e)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/problem/<problem_id>', methods = ['GET' , 'POST'])
@login_required
def problem(problem_id):
    """Display a specific problem"""
    #check if the problem is valid
    if problem_id in problems:
        #get the problem
        prob = problems[problem_id]
        #if it was a file submission
        if request.method == "POST":
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if not allowed_file(file.filename):
                flash('File extension not accepted')
                return redirect(request.url)
            if file:
                filename = str(datetime.utcnow().timestamp()) + '_' + prob.code + '_' + current_user.username + '.r'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                job = queue.enqueue_call(func = process_submission, args=(problem_id, current_user.username, filename,), result_ttl=5000)
                print(job.get_id())
                return redirect(url_for('get_results', job_key=job.get_id()))
        else:
            return render_template('problem.html', title='Problem', problem=prob)
    #if the problem is not valid return to initial page
    return redirect(url_for('index'))


@app.route('/get_file/<problem_id>/<file>')
@login_required
def get_file(problem_id, file):
    if problem_id in problems:
        prob = problems[problem_id]
        base_folder = app.config['PROBLEMS_DIR'] + '/' + prob.code + '/'
        if file in [i['file'] for i in prob.files]:
            return send_file(base_folder + file, attachment_filename=file)
        elif file in [i['input'] for i in prob.open_testcases] + [i['output'] for i in prob.open_testcases]:
            return send_file(base_folder + file, attachment_filename=file)
    return render_template('404.html', title='Invalid file')


@app.route('/results/<job_key>', methods=['GET'])
@login_required
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        result = UserProblemSubmission.query.filter_by(id=job.result).first()
        return render_template('result.html', title='Result', result = result)
    else:
        return render_template('result_wait.html', title='Results incoming...')


@app.route('/ranks', methods=['GET'])
@login_required
def ranks():
    result = UserProblemSubmission.query.filter_by(success=True).all()
    user_problem = dict()
    for i in result:
        if i.userid not in user_problem:
            user_problem[i.userid] = dict()
        user_problem[i.userid][i.problemid] = True
    ret = [(len(j[1].values()), j[0]) for j in user_problem.items()]
    ret.sort()
    return render_template('ranks.html', title='Ranks', players=ret)


@app.route('/problem_scoring/<problem_id>', methods=['GET'])
@login_required
def problem_scoring(problem_id):
    result = UserProblemSubmission.query.filter_by(problemid=problem_id).all()
    user_problem_pass = dict()
    user_problem_fail = dict()
    for i in result:
        if i.userid not in user_problem_pass:
            user_problem_pass[i.userid] = 0
        if i.userid not in user_problem_fail:
            user_problem_fail[i.userid] = 0
        if not i.success:
            user_problem_fail[i.userid] += 1
        if i.success:
            user_problem_pass[i.userid] += 1
    ret = list()
    for i in user_problem_pass.keys():
        ret.append((i, user_problem_pass[i], user_problem_fail[i]))
    ret.sort()
    return render_template('problem_scoring.html', title='Problem {} scores'.format(problem_id), players=ret)


