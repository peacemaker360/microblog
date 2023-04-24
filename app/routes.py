# app/routes.py
from flask import flash, jsonify, redirect, render_template, url_for, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db
from app.models import User, Post
from app.forms import LoginForm, RegisterForm, ResetPasswordForm,ResetPasswordRequestForm, EditProfileForm,DeleteProfileForm, EmptyForm, PostForm
from app.forms import QuerySelectDemoForm
from app.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!', 'success')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('search', None, type=str)
    search = "%{}%".format(query)
    if query:
        if len(query) < 3:
            flash('please provide more than 3 search characters', 'info')
            return redirect(url_for('explore'))
        else:
            posts = Post.query.filter(Post.body.like(search)).order_by(Post.timestamp.desc()).paginate(
                page=page, 
                per_page=app.config['POSTS_PER_PAGE'], 
                error_out=False
            )
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)
    form = EmptyForm()
    return render_template('user.html', 
                           title='User posts', 
                           user=user,
                           posts=posts,
                           form=form)

@app.route('/users')
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('search', None, type=str)
    search = "%{}%".format(query)
    if query:
        if len(query) < 3:
            flash('please provide more than 3 search characters', 'info')
            return redirect(url_for('users'))
        else:
            users = User.query.filter(User.username.like(search)).order_by(User.id.asc()).paginate(
                page=page, 
                per_page=app.config['USERS_PER_PAGE'], 
                error_out=False
            )
    else:
        users = User.query.order_by(User.id.asc()).paginate(
            page=page, 
            per_page=app.config['USERS_PER_PAGE'], 
            error_out=False
        )
    next_url = url_for('users', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('users', page=users.prev_num) \
        if users.has_prev else None
    return render_template('users.html', title='Users', users=users.items,
                           next_url=next_url, prev_url=prev_url)


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
        flash('Congratulations, you are now a registered user!', 'success')
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
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('user', username=current_user.username))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.about_me.data = current_user.about_me
        return render_template('edit_profile.html', title='Edit profile', form=form)
    else:
        flash('The admin profile may not be edited!', 'info')
        return redirect(url_for('user', username=current_user.username))

@app.route('/profile/delete/', methods=['GET','POST'])
@app.route('/profile/delete/<username>', methods=['GET','POST'])
@login_required
def delete_profile(username):
    if current_user.id != 1:
        flash('Only admin can delete profiles', 'error')
    if username is None:
        username = request.args.get('username', None, type=str)
    form = DeleteProfileForm(username)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        db.session.commit()
        flash('Profile has been deleted!', 'success')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = username
    return render_template('delete_profile.html', title='Delete profile', form=form)
 

   
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username), 'success')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username), 'info')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/resetpassword', methods=['GET','POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructuins on resetting you password.', 'info')
        return redirect(url_for('index'))
    return render_template('reset_password_request.html', title='Reset password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Reset link expired or invalid.', 'error')
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

#################################
# Custom testing routes
#################################

@app.route('/resetpassword', methods=['GET','POST'])
@login_required
def resetpassword():
    if current_user.id == 1:
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is None:
                flash('User not found.')
                return render_template('reset.html', title='Reset password', form=form)
            user.set_password(form.password.data)
            db.session.commit()
            flash('Password reset!', 'success')
            return redirect(url_for('login'))
        elif request.method == 'GET' and request.args.get('email', None, type=str) is not None:
            form.email.data = request.args.get('email', None, type=str)
            return render_template('reset.html', title='Reset password', form=form)
        return render_template('reset.html', title='Reset password', form=form)
    else:
        return "Admin required", 403

@app.route('/user_info', methods=['GET','POST'])
#@login_required
def user_info():
    if current_user.is_authenticated:
        resp = {"result": 200,
                "data": current_user.to_json()}
    else:
        resp = {"result": 401,
                "data": {"message": "user not login"}}
    return jsonify(**resp)



@app.route('/query_select_demo', methods=['GET','POST'])
def query_select_demo():
    form = QuerySelectDemoForm()
    form.users.query = db.session.query(User)
    if form.validate_on_submit() == True :
        user_id = int(form.users.data.id)
        return '<html><h3>Auswahl: User {}</h3></html>'.format(user_id)
    else:
        return render_template('query_select_demo.html', title='Select DB', form=form)