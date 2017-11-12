from flask import Flask, request
from flask_socketio import SocketIO, emit
import os
import sys

import compiler
import singleton

frozen = getattr(sys, 'frozen', False)

if frozen:
    root_dir = os.path.dirname(sys.executable)
else:
    root_dir = os.path.dirname(os.path.realpath(__file__))

sess_dir = os.path.join(root_dir, 'sessions')

app = Flask('javaplay', static_url_path='', static_folder=os.path.join(root_dir, 'static'))

import logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

socketio = SocketIO(app, async_mode='threading')

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

    def error(self, msg):
        self._emit('backend_error', {'description': msg})

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

def map_kill(sid):
    if sid in sid_program_map:
        sid_program_map[sid].kill()
        del sid_program_map[sid]

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
    map_kill(sid)
    sid_program_map[sid] = prog

@socketio.on('kill', namespace="/compiler")
def kill(msg):
    sid = request.sid
    print("== kill:", sid)
    map_kill(sid)

@socketio.on('stdin', namespace="/compiler")
def stdin(data):
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
    map_kill(sid)

if frozen or __name__ == "__main__":
    lockpath = os.path.join(root_dir, 'instance.lock')
    with singleton.InstanceFileLock(lockpath):
        if not os.path.isdir(sess_dir):
            os.makedirs(sess_dir)
        print()
        print("  +-----------------------------------------+")
        print("  | Compiler Backend listening on port 8040 |")
        print("  |    Keep this running in background...   |")
        print("  +-----------------------------------------+")
        print()
        socketio.run(app, port=8040)
