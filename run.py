#!/usr/bin/env python
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from mavapa import app


def simple(env, resp):
    resp("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello WSGI World"]


<<<<<<< HEAD
addr = app.config.get('BIND', '0.0.0.0')
port = app.config.get('PORT', 7001)
root = app.config.get('APPLICATION_ROOT', '/')
disp = DispatcherMiddleware(simple, {root: app})


if __name__ == "__main__":
    run_simple(addr, port, disp)
=======
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
>>>>>>> 6aae8003db92fa3b13961b51320c4ec4add591ce
