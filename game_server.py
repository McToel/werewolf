from flask import Flask, Response, redirect, url_for, request, session, abort, jsonify, escape
import flask
from flask_login import LoginManager, UserMixin, current_user, \
            login_required, login_user, logout_user 
import os
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

import json
import random
from time import sleep

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

@app.route('/favicon.ico')
def favicon():
    app.send_static_file('favicon.ico')
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

class User(UserMixin):
    def __init__(self, name):
        self.name = name
        self.id = name
        self.sid = None
        self.alive = True
        self.role = ''
    def copy(self):
        return {'name':self.name, 'alive':self.alive, 'role':self.role}
    @property
    def as_json(self):
        return {'name':self.name, 'alive':self.alive}

    @property
    def as_gamemaster_json(self):
        return {'name':self.name, 'alive':self.alive, 'role':self.role}

users = {'gamemaster': User('gamemaster')}
users['gamemaster'].alive = False
role_rooms = []

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

@app.route('/')
@login_required
def home():
    username = current_user.name
    if username == 'gamemaster':
        return redirect('/gamemaster')
    if not username in users:
        users[username] = User(username)
    return flask.render_template('game.html')

@app.route('/gamemaster')
@login_required
def gamemaster():
    if current_user.name != 'gamemaster':
        return redirect('/')
    print('gamemaster joined')
    return flask.render_template('gamemaster.html')
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = escape(request.form['username'])
        user = User(username)
        login_user(user)
        users[username] = user
        return redirect(request.args.get("next"))
    else:
        return flask.render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    username = current_user.name
    if not username == 'gamemaster':
        emit('remove_user', {'target':username}, broadcast=True, namespace='')
        users.pop(username, None)
        session.clear()
    logout_user()
    return redirect('/')

@socketio.on('connect')
def test_connect():
    try:
        users[current_user.name].update = True
        users[current_user.name].update_head = True
    except KeyError:
        pass
    username = current_user.name
    if username != 'gamemaser':
        try:
            emit('set_role', {'role':users[username].role, 'name':username})
            emit('set_name', {'name':username})
        except KeyError:
            pass
        join_room('_users')
    print('user', username, 'connected')

@socketio.on('disconnect')
def test_disconnect():
    try:
        print(current_user.name, 'disconnected')
    except:
        print('User disconnected')

@socketio.on('join_role_rooms')
def join_rooms(json_data):
    global role_rooms
    old_room = json_data['old_room']
    leave_room(old_room)
    username = current_user.name
    role = users[username].role
    join_room(role)
    sleep(2)
    emit('set_role', {'role':role, 'name':username}, room=role)

@socketio.on('private_vote')
def handle_private_vote(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    emit('update_vote', {'voter':username, 'target':target_user, 'type':'_private_vote'}, room=users[username].role)

@socketio.on('public_vote')
def handle_public_vote(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    emit('update_vote', {'voter':username, 'target':target_user, 'type':'_public_vote'}, broadcast=True)

@socketio.on('load_game')
def load_game():
    username = current_user.name
    users[username].sid = request.sid
    emit('append_user', users[username].as_json, room='_users', namespace='')
    emit('append_user', users[username].as_gamemaster_json, room=users['gamemaster'].sid, namespace='')
    if username == 'gamemaster':
        for user in users:
            emit('append_user', users[user].as_gamemaster_json)
    else:
        for user in users:
            emit('append_user', users[user].as_json)

@socketio.on('set_roles')
def handle_set_roles(json_data):
    global role_rooms
    role_rooms = []
    roles = json_data['roles']
    random.shuffle(roles)
    if len(roles) == len(users) - 1:
        for key in users:
            username = users[key].name
            if username != 'gamemaster':
                emit('append_user', users[username].as_json, room='_users', namespace='')
                emit('append_user', users[username].as_gamemaster_json, room=users['gamemaster'].sid, namespace='')
                old_role = users[key].role
                users[key].role = roles.pop()
                join_room(users[key].role)
                users[key].alive = True
                users[key].update_head = True
                emit('join_role_rooms', {'old_room':old_role}, room=users[key].sid)

@socketio.on('reset_votes')
def handle_reset_votes():
    for username in users:
        emit('remove_vote', {'voter':username, 'type':'_private_vote'}, broadcast=True)
        emit('remove_vote', {'voter':username, 'type':'_public_vote'}, broadcast=True)

@socketio.on('kill')
def handle_kill(json_data):
    target = json_data['target_user']
    users[target].alive = False
    emit('kill_user', {'target':target}, broadcast=True)

@socketio.on('poke')
def handle_poke(json_data):
    target_user = json_data['target_user']
    emit('flash', room=users[target_user].sid)

@socketio.on('send_msg')
def handle_send_msg(json_data):
    username = current_user.name
    target_user = json_data['target_user']
    emit('receive_msg', {'msg': username + ': ' + escape(json_data['msg'])}, room=users[target_user].sid)

@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')

if __name__ == "__main__":
    socketio.run(app, host= '0.0.0.0', port=5000)