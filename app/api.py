# app/api.py
from app import app, db
from app.errors import bad_request, error_response
from app.models import User, Post
from flask import jsonify, request, url_for, abort
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from datetime import datetime

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None

@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)

@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)
############################################################
# API Auth handling
############################################################
@app.route('/api/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return jsonify({'token': token})

# Token ungültig machen
@app.route('/api/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204

############################################################
## GET FUNCTION ##
############################################################
@app.route('/api/users', methods=['GET'])
@token_auth.login_required
def get_users():
    data = User.to_collection()
    return jsonify(data)

@app.route('/api/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    data = User.query.get_or_404(id).to_dict()
    return jsonify(data)

@app.route('/api/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    data = user.followers_to_collection()
    return jsonify(data)

@app.route('/api/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    data = user.followed_to_collection()
    return jsonify(data)

@app.route('/api/users/<int:id>/posts', methods=['GET'])
@token_auth.login_required
def get_posts(id):
    user = User.query.get_or_404(id)
    data = user.posts_to_collection()
    return jsonify(data)

@app.route('/api/users/<int:id>/posts/<int:postid>', methods=['GET'])
@token_auth.login_required
def get_userpostsbyid(id, postid):
    user = User.query.get_or_404(id)
    data = user.posts_byid_to_collection(postid)
    return jsonify(data)


@app.route('/api/posts', methods=['GET'])
@token_auth.login_required
def get_allposts():
    data = Post.to_collection()
    return jsonify(data)

############################################################
## POST FUNCTION ##
############################################################
# Endpunkt für User-Registrierung
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if not data:
        return bad_request('malformed request')
    if 'username' not in data or 'email' not in data or 'password' not in data:
        usernameOk = 'username' in data
        emailOk = 'email' in data
        passwordOk = 'password' in data
        #return jsonify(usernameOk)
        message = "must include username, email and password fields. (username: {}, email: {}, password: {})".format(usernameOk, emailOk, passwordOk)
        return bad_request(message)
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('get_user', id=user.id)
    return response

# Endpunkt für Erzuegen eines Posts
@app.route('/api/users/<int:id>/post', methods=['POST'])
@token_auth.login_required
def create_post(id):
    # Nur der eigene user oder admin dürfen posts absetzten
    if token_auth.current_user().id != id or token_auth.current_user().id != 1:
        abort(403) # Abbruch, Response mit Status-Code 403
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if not data:
        return bad_request('malformed request')
    if 'body' not in data:
        bodyOk = 'body' in data
        message = "must include body fields. (body: {})".format(bodyOk)
        return bad_request(message)
    post = Post()
    post.body = data['body']
    post.user_id = user.id
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())

############################################################
## PUT FUNCTION ##
############################################################
# Endpunkt für User-änderungen
@app.route('/api/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    # Nur die Informationen des eigenen Users können geändert werden
    if token_auth.current_user().id != id:
        abort(403) # Abbruch, Response mit Status-Code 403
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and \
        User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
        User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())


# Endpunkt für Post-änderungen
@app.route('/api/users/<int:userid>/posts/<int:postid>', methods=['PUT'])
@token_auth.login_required
def update_post(userid,postid):
    # Nur die Posts des eigenen Users können geändert werden
    if token_auth.current_user().id != userid:
        abort(403) # Abbruch, Response mit Status-Code 403
    user = User.query.get_or_404(userid)
    data = request.get_json() or {}
    if not data:
        return bad_request('malformed request')
    if 'body' not in data:
        bodyOk = 'body' in data
        message = "must include body fields. (body: {})".format(bodyOk)
        return bad_request(message)
    post = Post.query.get_or_404(postid)
    if not post:
        return bad_request('post not found.')
    if post.user_id != userid:
         abort(403) # Abbruch, Response mit Status-Code 403
    post.body = data['body']
    post.timestamp = datetime.utcnow()
    db.session.commit()
    return jsonify(post.to_dict())


############################################################
## DELETE FUNCTION ##
############################################################

# Endpunkt für User-löschung
@app.route('/api/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    # Nur der admin darf user löschen
    if token_auth.current_user().id != 1:
        abort(403) # Abbruch, Response mit Status-Code 403
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(user.to_dict())