from flask import Flask, request
from flask_socketio import SocketIO, emit

import compiler

app = Flask('javaplay', static_url_path='', static_folder='static')
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

sid_program_map = {}

@app.route('/')
def root():
    return app.send_static_file('index.html')

@socketio.on('compile', namespace="/compiler")
def compile(msg):
    sid = request.sid
    print("== compile:", sid)
    prog = compiler.Program(msg, sid, Callbacks(socketio, sid))
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

if __name__ == "__main__":
    socketio.run(app, port=8040)
