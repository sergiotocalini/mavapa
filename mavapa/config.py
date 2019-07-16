#!/usr/bin/env python
# import os


class Default(object):
    BIND = '0.0.0.0'
    PORT = 7001
    CSRF_ENABLED = True
    SECRET_KEY = 'WYmpcUG1UA2ORJgRJoYt'
    APPLICATION_ROOT = ''
    CDN_BOOTSTRAP = "//maxcdn.bootstrapcdn.com/bootstrap/3.3.7"
    CDN_FONTAWESOME = "//maxcdn.bootstrapcdn.com/font-awesome/4.7.0"
    DEBUG = False
    DB_DEBUG = False
    DB_TYPE = 'mysql'
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'
    DB_NAME = 'mavapa'
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    
class Production(Default):
    DB_USER = 'app_mavapa'
    DB_PASS = 'nooX3pegh5loh8T'

    
class Staging(Default):
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'

    
class Development(Default):
    DEBUG = True
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'

    
class Local(Default):
    APPLICATION_ROOT = '/mavapa'
    SECRET_KEY = 'insecure0123456789'
    DEBUG = True
    DB_DEBUG = True
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'


class Docker(Local):
    DB_HOST = 'mysql'
