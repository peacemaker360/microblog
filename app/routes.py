# app/routes.py
from flask import flash, jsonify, redirect, render_template, url_for, request
from app import app, db
from app.forms import LoginForm, RegisterForm, ResetPasswordForm, EditProfileForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
        'author': {'username': 'Paul'},
        'body': 'Schöner Abend hier in Zürich!'
        },
        {
        'author': {'username': 'Susanne'},
        'body': 'Der Unterricht war heute mal gut!'
        }
    ]
    return render_template('index.html', 
                           title='Home', 
                           posts=posts)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {
        'author': user,
        'body': 'Test post #1'
        },
        {
        'author': user,
        'body': 'Test post #2'
        }
    ]
    return render_template('user.html', 
                           title='User posts', 
                           user=user,
                           posts=posts)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next') # Rückkehr-Pfad
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', 
                           title="Sign In", 
                           form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/profile/edit', methods=['GET','POST'])
@login_required
def edit_profile():
    if current_user.id != 1:
        form = EditProfileForm(current_user.username)
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.about_me = form.about_me.data
            db.session.commit()
            flash('Your profile has been updated!')
            return redirect(url_for('user', username=current_user.username))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.about_me.data = current_user.about_me
        return render_template('edit_profile.html', title='Edit profile', form=form)
    else:
        flash('The admin profile may not be edited!')
        return redirect(url_for('user', username=current_user.username))

@app.route('/resetpassword', methods=['GET','POST'])
@login_required
def resetpassword():
    if current_user.id == 1:
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None:
                flash('User not found.')
            user.set_password(form.password.data)
            db.session.commit()
            flash('Password reset!')
            return redirect(url_for('login'))
        return render_template('reset.html', title='Reset password', form=form)
    else:
        return "Admin required", 401

@app.route('/user_info', methods=['GET','POST'])
#@login_required
def user_info():
    if current_user.is_authenticated:
        resp = {"result": 200,
                "data": current_user.to_json()}
    else:
        resp = {"result": 401,
                "data": {"message": "user no login"}}
    return jsonify(**resp)