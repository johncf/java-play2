from gevent.subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from gevent.queue import Queue, Empty
import os
import re
from gevent import Greenlet

root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sessions")
if not os.path.exists(root_dir):
    os.makedirs(root_dir)

class_pat = re.compile("^(public )?class (?P<name>\w+)", re.MULTILINE)
dir_pat = re.compile("^[a-z0-9]+$")

def extract_class_name(source):
    m = class_pat.match(source)
    if m is not None:
        return m.group("name")
    else:
        return "BadName"

def write_file(path, contents):
    f = open(path, "w")
    f.write(contents)
    f.close()

def reset_dir(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)
    os.makedirs(path)

def read2queue(key, stream, notifq):
    while True:
        out = stream.read1(256)
        if out:
            notifq.put((key, out))
        else:
            notifq.put((key, None))
            break

class Program:
    # callbacks must have the following methods:
    #     compiled(ecode, logs), stdout(data), stderr(data), done(ecode)
    def __init__(self, source, dirname, callbacks):
        if type(source) is not str and len(source) < 9:
            raise ValueError("source must be a non-empty string")
        if dir_pat.match(dirname) is None:
            raise ValueError("dirname must be alphanumeric")
        self._name = extract_class_name(source)
        self._dir = os.path.join(root_dir, dirname)
        reset_dir(self._dir)
        write_file(os.path.join(self._dir, self._name + ".java"), source)
        self._queue = Queue()
        self._cbs = callbacks

    def _compile(self):
        proc = Popen(["javac", "-Xlint", self._name + ".java"], cwd=self._dir, stdout=PIPE, stderr=STDOUT)
        try:
            out, _ = proc.communicate(timeout=5)
            ecode = proc.returncode
        except TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
            ecode = None
        return (ecode, out)

    def _execute(self):
        return Popen(["java", self._name], cwd=self._dir, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def spawn_bg(self):
        t = Greenlet(spawn, self)
        t.start()
        return t

    def kill(self):
        self._queue.put(("kill", None))

    def stdin(self, data):
        self._queue.put(("stdin", data))

def spawn(program):
    ecode, logs = program._compile()
    program._cbs.compiled(ecode, logs)
    if ecode != 0:
        program._cbs.done(None)
        return
    proc = program._execute()
    outt = Greenlet(read2queue, 'stdout', proc.stdout, program._queue)
    outt.start()
    errt = Greenlet(read2queue, 'stderr', proc.stderr, program._queue)
    errt.start()
    done = False
    while True:
        try:
            if not done:
                key, data = program._queue.get(timeout=1)
            else:
                outt.join()
                errt.join()
                key, data = program._queue.get_nowait()

            if key == 'stdin':
                if data is None:
                    proc.stdin.close()
                else:
                    proc.stdin.write(data)
                    proc.stdin.flush()
            elif key == 'stdout':
                if data is not None:
                    program._cbs.stdout(data)
            elif key == 'stderr':
                if data is not None:
                    program._cbs.stderr(data)
            elif key == 'kill':
                proc.kill()
        except Empty:
            if done:
                break

        if proc.poll() is not None:
            done = True

    program._cbs.done(proc.returncode)
