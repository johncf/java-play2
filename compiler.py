from gevent.subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from gevent.queue import Queue, Empty
from gevent import Greenlet
import os
import re

class_pat = re.compile("^(public )?class (?P<name>\w+)", re.MULTILINE)

def extract_class_name(source):
    m = class_pat.search(source)
    if m is not None:
        return m.group("name")
    else:
        return "BadName"

def write_file(path, contents):
    f = open(path, "w")
    f.write(contents)
    f.close()

def read2queue(key, stream, notifq, limit=2048):
    total = 0
    while True:
        if total > limit:
            stream.close()
            notifq.put((key, b'%\n\n>>> output limit exceeded! stream closed <<<'))
            break
        out = stream.read1(256)
        if out:
            notifq.put((key, out))
            total += len(out)
        else:
            notifq.put((key, None))
            break

class Program:
    # callbacks must have the following methods:
    #     compiled(ecode, logs), stdout(data), stderr(data), stdin_ack(data), done(ecode)
    def __init__(self, source, dirpath, callbacks):
        if type(source) is not str and len(source) < 9:
            raise ValueError("source must be a non-empty string")
        if not os.path.isdir(dirpath):
            raise ValueError("dirpath must be a valid directory")
        self._name = extract_class_name(source)
        self._dir = dirpath
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
        if (type(data) != bytes):
            raise TypeError("data must be bytes")
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
                    program._cbs.stdout(data)
                    try:
                        proc.stdin.flush()
                    except OSError as e:
                        print("== OSError:", e)
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
