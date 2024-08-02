#!/usr/bin/env python
# Default configuration
import os

BIND = '0.0.0.0'
PORT = 7001
CSRF_ENABLED = True
SECRET_KEY = os.urandom(24)
APPLICATION_ROOT = ''
DEBUG = False
JSONIFY_PRETTYPRINT_REGULAR = False
PONY_DEBUG = False
PONY_GENERATE_MAPPING = dict(
    create_tables=True,
    check_tables=True,
)

PONY = dict(
    provider="sqlite",
    filename=":memory:"
)
