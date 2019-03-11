#!/usr/bin/env python
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from mavapa import app


def simple(env, resp):
    """A wrapper of a prefix"""
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return [b"Hello WSGI World"]


context = app.config.get('APPLICATION_ROOT', '/')
dispatcher = DispatcherMiddleware(
    simple, {context: app}
)  # pylint: disable=I0011,C0103


if __name__ == "__main__":
    run_simple(
        app.config.get('BIND', '0.0.0.0'),
        app.config.get('PORT', 7001),
        dispatcher
    )
