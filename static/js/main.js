Split(['#left', '#right'], {
  gutterSize: 8
});
Split(['#rtop', '#rbot'], {
  sizes: [40, 60],
  direction: 'vertical',
  gutterSize: 8
});

const sourceTmpl = "public class Test {\n    public static void main(String[] args) {\n    }\n}";
const storeOk = typeof(Storage) !== "undefined";
function initIndex() {
  var idx = storeOk && +localStorage.next || 0;
  var bang = window.location.hash.substr(2);
  if (/^[0-7]$/.test(bang)) {
    return +bang;
  } else {
    if (storeOk) {
      localStorage.next = (idx + 1) % 8;
      delete localStorage[localStorage.next];
    }
    history.replaceState('', document.title, window.location.pathname + "#!" + idx);
    return idx;
  }
}

const sourceIdx = initIndex();
function getSource() {
  return storeOk && localStorage[sourceIdx] || sourceTmpl;
}
function setSource(source) {
  if (storeOk) {
    localStorage[sourceIdx] = source;
  }
}

const editor = ace.edit("editor");
editor.setTheme("ace/theme/tomorrow");
editor.session.setMode("ace/mode/java");
editor.session.doc.setNewLineMode("unix");
editor.setValue(getSource(), 1);

function htmlEscape(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const log = document.getElementById("logs");
var log_pos = 0;
function logClear() {
  log.innerHTML = "";
  log_pos = 0;
}
function logAppend(str, is_volatile) {
  log.innerHTML = log.innerHTML.substring(0, log_pos) + htmlEscape(str);
  if (!is_volatile) {
    log_pos = log.innerHTML.length;
  }
}

const out = document.getElementById("output");
function outClear() {
  out.innerHTML = "";
}
function outAppend(str) {
  out.innerHTML += htmlEscape(str);
}

const compile_button = document.getElementById("compile");
const kill_button = document.getElementById("kill");
const stdin_input = document.getElementById("stdin");

function fatalError(msg) {
  logClear();
  logAppend(msg, true);
  compile_button.disabled = true;
  kill_button.disabled = true;
  stdin_input.disabled = true;
}

const socket = io("/compiler");
socket.on('connect', function() {
  logAppend("Click \"Compile & Execute\" when ready.", true);
  compile_button.disabled = false;
  kill_button.disabled = true;
  stdin_input.disabled = true;
});
socket.on('disconnect', function() {
  fatalError("Connection with compiler lost. Please rerun the backend.");
});
socket.on('backend_error', function(e) {
  fatalError(e.description);
});
socket.on('started', function(msg) {
  logAppend("Compiling...", true);
  kill_button.disabled = false;
});
socket.on('compiled', function(msg) {
  if (msg.ecode == 0) {
    if (msg.logs) {
      logAppend("Compiled with logs:\n" + msg.logs, false);
    } else {
      logAppend("Compiled successfully.\n", false);
    }
    logAppend("Executing...", true);
  } else if (msg.ecode == null) {
    logAppend("Compilation failed. Please try again...\n", false);
  } else if (msg.logs) {
    logAppend("Compiler reported errors:\n" + msg.logs, false);
  } else {
    logAppend("Compiler stopped!\n", false);
  }
  stdin_input.disabled = false;
  stdin_input.focus();
});
socket.on('stdout', function(msg) {
  outAppend(msg.data);
  out.scrollTop = out.scrollHeight;
});
socket.on('stderr', function(msg) {
  outAppend(msg.data);
  out.scrollTop = out.scrollHeight;
});
socket.on('stdin_ack', function(msg) {
  outAppend(msg.data);
  out.scrollTop = out.scrollHeight;
});
socket.on('done', function(msg) {
  if (msg.ecode == 0) {
    logAppend("Execution completed.\n", false);
  } else if (msg.ecode !== null) {
    logAppend("Execution stopped. [" + msg.ecode + "]\n", false);
  }
  compile_button.disabled = false;
  kill_button.disabled = true;
  stdin_input.disabled = true;
  editor.focus();
});

compile_button.onclick = function(e) {
  var source = editor.getValue();
  logClear();
  outClear();
  logAppend("Compilation requested...", true);
  socket.emit("compile", source);
  compile_button.disabled = true;
  setSource(source);
}
kill_button.onclick = function(e) {
  logAppend("Trying to stop...", true);
  socket.emit('kill', null);
  kill_button.disabled = true;
}
stdin_input.onkeypress = function(e) {
  if (e.keyCode == 13) {
    socket.emit('stdin', stdin_input.value + "\n");
    stdin_input.value = "";
  }
}

window.onbeforeunload = function(e) {
  setSource(editor.getValue());
  socket.close();
}
