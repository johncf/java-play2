# Java Playground

A web-based Java compiler frontend to play with single-source console programs. [UI Demo][]

[UI Demo]: https://codepen.io/johncf/full/dZWXpW

## Requirements

- Python 3.4+
- [Flask](http://flask.pocoo.org/)
- [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO)
- A modern browser
  - Supporting [`localStorage`][], [`history.replaceState`][], [`const`][], [`box-sizing`][], [`flex`][]
  - Supposedly Firefox 29+, Chrome 29+, Edge, Safari 9+, IE 11, Opera 17+
- `javac` and `java` in `PATH` when executing server ([example batch file](https://gist.github.com/johncf/a98cd3aa49491c5f58372566883e7810) which does this).

[`localStorage`]: https://caniuse.com/#feat=const
[`history.replaceState`]: https://caniuse.com/#feat=history
[`const`]: https://caniuse.com/#feat=const
[`box-sizing`]: https://caniuse.com/#feat=css3-boxsizing
[`flex`]: https://caniuse.com/#feat=flexbox

## Motivation

This was developed to provide an easy-to-use UI for students learning programming for the first time, due to a complete lack of user-friendly, lightweight and bug-free IDE for Java.

As such, this is intended to be run and used locally, since its performance won't scale well to more than a handful of users, and more importantly, it is very insecure for the open web (for starters, program execution is not sandboxed).

## Acknowledgements

Code from the following projects are included in this repository:

- [Ace Editor](https://ace.c9.io/)
- [Split.js](http://nathancahill.github.io/Split.js/)
- [Socket.io](https://socket.io/)

## Building a Frozen Executable

- Install all dependencies

  ```sh
  python -m pip install flask flask-socketio
  ```

- Install `cx-Freeze` v6.0

  ```sh
  python -m pip install cx-Freeze==6.0b1
  ```

- Run build script

  ```sh
  python setup.py build
  ```

You can find similarly built binaries [here](https://github.com/johncf/java-play2/releases).
