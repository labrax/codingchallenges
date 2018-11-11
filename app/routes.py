from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import UserInformation


@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


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


@app.route("/sections")
@login_required
def sections():
    """List problems"""
    return "We good"


@app.route('/section/<int:section_id>', methods = ['GET' , 'POST'])
@login_required
def section(section_id):
    """Display a specific section"""
    return "This section: {}".format(section_id)


@app.route('/problem/<int:problem_id>', methods = ['GET' , 'POST'])
@login_required
def problem(problem_id):
    """Display a specific section"""
    return "This problem: {}".format(problem_id)
