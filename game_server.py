from flask import Flask, Response, redirect, url_for, request, session, abort, jsonify, escape
import flask
from flask_login import LoginManager, UserMixin, current_user, \
            login_required, login_user, logout_user 
import os
from flask_session import Session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

import json
import random

app = Flask(__name__)

CORS(app)

app.secret_key = os.urandom(12)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

socketio = SocketIO(app, cors_allowed_origins='*', manage_session=False)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, name):
        self.name = name
        self.id = self.name
        self.alive = True
        self.role = ''
        self.public_votes = []
        self.private_votes = []
        self.do_flash = True
        self.update = True
        self.update_head = True
        self.message = ''
    def copy(self):
        return {'name':self.name, 'alive':self.alive, 'role':self.role, 
            'public_votes':self.private_votes, 'private_votes':self.private_votes, 
            'do_flash':self.do_flash, 'update':self.update}
    @property
    def as_json(self):
        return {'name':self.name, 'alive':self.alive, 'merolessage':self.message,
            'public_votes':self.public_votes, 'private_votes':self.private_votes}

    @property
    def as_gamemaster_json(self):
        return {'name':self.name, 'alive':self.alive, 'role':self.role,
            'votes':self.public_votes + self.private_votes}

users = {'gamemaster': User('gamemaster')}
users['gamemaster'].alive = False

def update_users(user=None, role=None):
    if user:
        users[user].update = True
    elif role:
        try:
            users['gamemaster'].update = True
        except KeyError:
            pass
        for key in users:
            if users[key].role == role:
                users[key].update = True
    else:
        for key in users:
            users[key].update = True

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# @app.route('/static/js/<path:path>')
# def send_js(path):
#     return flask.send_from_directory('/static/js/', path, mimetype='text/javascript')

# some protected url
@app.route('/')
@login_required
def home():
    username = current_user.name
    if username == 'gamemaster':
        return redirect('/gamemaster')
    if not username in users:
        users[username] = User(username)
        update_users()
    return flask.render_template('game.html')

@app.route('/gamemaster')
@login_required
def gamemaster():
    if current_user.name != 'gamemaster':
        return redirect('/')
    print('gamemaster joined')
    return flask.render_template('gamemaster.html')
 
# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = escape(request.form['username'])
        user = User(username)
        login_user(user)
        users[username] = User(username)
        update_users()
        return redirect(request.args.get("next"))
    else:
        return flask.render_template('login.html')
        # return Response('''
        # <form action="" method="post">
        #     <p><input type=text name=username>
        #     <p><input type=submit value=Login>
        # </form>
        # ''')

# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    if not current_user.name == 'gamemaster':
        users.pop(current_user.name, None)
    logout_user()
    return redirect('/')
    #return Response('<p>Logged out</p>')

@socketio.on('connect')
def test_connect():
    try:
        users[current_user.name].update = True
        users[current_user.name].update_head = True
    except KeyError:
        pass
    print('user', current_user.name, 'connected')
    # emit('flash')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@socketio.on('private_vote')
def handle_public_vote(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    for key in users:
        if username in users[key].private_votes:
            users[key].private_votes.remove(username)
    users[target_user].private_votes.append(username)
    update_users(role=users[username].role)

@socketio.on('public_vote')
def handle_private_vote(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    for key in users:
        if username in users[key].public_votes:
            users[key].public_votes.remove(username)
    users[target_user].public_votes.append(username)
    update_users()

@socketio.on('set_roles')
def handle_set_roles(json_data):
    roles = json_data['roles']
    random.shuffle(roles)
    if len(roles) == len(users) - 1:
        for key in users:
            if users[key].name != 'gamemaster':
                users[key].role = roles.pop()
                users[key].alive = True
                users[key].update_head = True
        update_users()

@socketio.on('reset_votes')
def handle_reset_votes():

    for key in users:
        users[key].private_votes = []
        users[key].public_votes = []
    users['gamemaster'].update = True

@socketio.on('kill')
def handle_kill(json_data):
    target_user = json_data['target_user']
    users[target_user].alive = False
    update_users()

@socketio.on('poke')
def handle_poke(json_data):
    target_user = json_data['target_user']
    users[target_user].do_flash = True

@socketio.on('send_msg')
def handle_send_msg(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    users[target_user].message = username + ': ' + escape(json_data['msg'])
    users[target_user].update_head = True

@socketio.on('update_gamemaster')
def handle_update_gamemaster():
    if users['gamemaster'].do_flash:
        emit('flash')
        users['gamemaster'].do_flash = False

    if users['gamemaster'].update:
        emit('update_gamemaster_display', {key:users[key].as_gamemaster_json for key in users})
        users['gamemaster'].update = False

    if users['gamemaster'].update_head:
            emit('update_head', {'name':'gamemaster', 'role':'gamemaster', 'msg':users['gamemaster'].message})
            users['gamemaster'].update_head = False

@socketio.on('update_data')
def handle_update_data():
    username = current_user.name
    try:
        if users[username].do_flash:
            emit('flash')
            users[username].do_flash = False

        if users[username].update:
            data_to_update = {key:users[key].as_json for key in users}
            for user in data_to_update:
                private_voters = []
                for voter in data_to_update[user]['private_votes']:
                    if users[voter].role == users[username].role:
                        private_voters.append(voter)
                data_to_update[user]['private_votes'] = private_voters
            emit('update_display', data_to_update)
            users[username].update = False

        if users[username].update_head:
            emit('update_head', {'name':username, 'role':users[username].role, 'msg':users[username].message})
            users[username].update_head = False

    except KeyError:
        redirect('/')

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')

if __name__ == "__main__":
    socketio.run(app, host= '0.0.0.0', port=5000)