#!/usr/bin/env python
# Default configuration

BIND = '0.0.0.0'
PORT = 7001
CSRF_ENABLED = True
SECRET_KEY = 'WYmpcUG1UA2ORJgRJoYt'
APPLICATION_ROOT = ''
DEBUG = False
PONY_DEBUG = False
PONY_GENERATE_MAPPING = dict(
    create_tables  = True,
    check_tables   = True
)
PONY = dict(
    provider = "sqlite",
    filename = ":memory:"
)
JSONIFY_PRETTYPRINT_REGULAR = False
