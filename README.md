# Java Playground

A web-based Java playground for single-file console applications.

## Requirements

- Python 3.4+
- [Gevent](http://www.gevent.org/)
- [Flask](http://flask.pocoo.org/)
- [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO)

## Motivation

This was developed to provide an easy-to-use UI for students learning programming for the first time, due to a complete lack of user-friendly, lightweight and bug-free IDE for Java.

As such, this is intended to be run and used locally, since its performance won't scale well to more than a handful of users, and more importantly, it is very insecure for the open web (for starters, program execution is not sandboxed).
