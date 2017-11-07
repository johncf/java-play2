from flask import Flask, request
from flask_socketio import SocketIO, emit
import os
import sys

import compiler

frozen = getattr(sys, 'frozen', False)

if frozen:
    root_dir = os.path.dirname(sys.executable)
else:
    root_dir = os.path.dirname(os.path.realpath(__file__))

sess_dir = os.path.join(root_dir, 'sessions')

app = Flask('javaplay', static_url_path='', static_folder=os.path.join(root_dir, 'static'))
socketio = SocketIO(app)

class Callbacks:
    def __init__(self, socketio, sid):
        self._sock = socketio
        self._sid = sid
        self._emit('started', {})

    def _emit(self, key, msg):
        self._sock.emit(key, msg, room=self._sid, namespace="/compiler")

    def compiled(self, ecode, logs):
        self._emit('compiled', {'ecode': ecode, 'logs': logs.decode('utf-8')})

    def stdout(self, data):
        self._emit('stdout', {'data': data.decode('utf-8')})

    def stderr(self, data):
        self._emit('stderr', {'data': data.decode('utf-8')})

    def stdin_ack(self, data):
        self._emit('stdin_ack', {'data': data.decode('utf-8')})

    def done(self, ecode):
        self._emit('done', {'ecode': ecode})

def reset_dir(path):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(path)

sid_program_map = {}

@app.route('/')
def root():
    return app.send_static_file('index.html')

@socketio.on('compile', namespace="/compiler")
def compile(msg):
    sid = request.sid
    print("== compile:", sid)
    prog_dir = os.path.join(sess_dir, sid)
    reset_dir(prog_dir)
    prog = compiler.Program(msg, prog_dir, Callbacks(socketio, sid))
    prog.spawn_bg()
    sid_program_map[sid] = prog

@socketio.on('kill', namespace="/compiler")
def kill(msg):
    sid = request.sid
    print("== kill:", sid)
    if sid in sid_program_map:
        sid_program_map[sid].kill()

@socketio.on('stdin', namespace="/compiler")
def kill(data):
    sid = request.sid
    print("== stdin:", sid)
    if sid in sid_program_map:
        sid_program_map[sid].stdin(data.encode('utf-8'))

@socketio.on('connect', namespace="/compiler")
def connect():
    print("== connected:", request.sid)

@socketio.on('disconnect', namespace="/compiler")
def disconnect():
    sid = request.sid
    print("== disconnected:", sid)
    if sid in sid_program_map:
        del sid_program_map[sid]

if frozen or __name__ == "__main__":
    if not os.path.isdir(sess_dir):
        os.makedirs(sess_dir)
    socketio.run(app, port=8040)
