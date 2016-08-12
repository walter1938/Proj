#!/usr/bin/env python
import os
import json
import requests
from json import dumps as make_json
from flask import Flask, abort, request, jsonify, g, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'IDDQD'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    """
     Here and so on further username is an email of the user,
     but it's stored under username variable for better understanding of the code
    """
    username = db.Column(db.String(64), index = True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_user():
    # creating a new user and storing him with a hashed password
    # into a db
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    # get user by his id
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    # generating a token for user after validating his credentials
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/api/create_post', methods = ['POST'])
@auth.login_required
def create_post():
    """
    Post creation view. It assigns values from the terminal
    in the json format to the dict 'post' which is a value
    from a list 'posts'.
    """
    if not request.json or not 'title' in request.json:
        abort(400)
    post = {
        'id': posts[-1]['id'] + 1,
        'title': request.json['title'],
        'body': request.json.get('body', ''),
    }
    posts.append(post)
    return make_json({'post': post}), 201


posts = [
    {
        'id': 1,
        'title': 'test title',
        'body': 'test body',
    }
]


@app.route('/api/create_post/all/<int:page>', methods=['GET'])
@auth.login_required
def get_all_posts(page):
    """
    This function returns users' posts with pagination by 2.
    It's simply making chunks from a 'posts' list and returns
    these chunks by a number provided by user ('page').
    """
    paginate = [posts[e:e+2] for e in xrange(0, len(posts), 2)]
    return jsonify({'posts':paginate[page]})


@app.route('/api/create_post/<int:post_id>', methods = ['GET'])
@auth.login_required
def get_post(post_id):
    # Gets a post with post id provided by user.
    for post in posts:
        if post['id'] == post_id:
            return jsonify({'post': post})
    abort(404)


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)
