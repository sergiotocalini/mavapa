#!/usr/bin/env python
import os

class Config(object):
    BIND = '0.0.0.0'
    PORT = 7001
    CSRF_ENABLED = True
    SECRET_KEY = 'WYmpcUG1UA2ORJgRJoYt'
    APPLICATION_ROOT = ''
    CDN_BOOTSTRAP = "//cdn.corpam.com.ar/bootstrap/stable"
    CDN_FONTAWESOME = "//cdn.corpam.com.ar/fontawesome/stable"
    CDN_COMMON = '//cdn.corpam.com.ar/common/stable'
    CDN_DATATABLES = '//cdn.corpam.com.ar/datatables/stable'
    #CDN_MAVAPA = '//cdn.corpam.com.ar/mavapa/stable'
    DEBUG = False
    DB_DEBUG = False
    DB_TYPE = 'mysql'
    DB_PORT = 3306
    DB_NAME = 'mavapa'
    
class Production(Config):
    DB_HOST = 'mysql01.prd.srv.hon.ar.internal'
    DB_USER = 'app_mavapa'
    DB_PASS = 'nooX3pegh5loh8T'
    
class Staging(Config):
    DB_HOST = 'mysql.stg.srv.hon.ar.internal'
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'
    
class Development(Config):
    DEBUG = True
    DB_HOST = 'mysql.dev.srv.hon.ar.internal'
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'

class Local(Config):
    APPLICATION_ROOT = '/mavapa'
    SECRET_KEY = 'insecure0123456789'
    DEBUG = True
    DB_DEBUG = True
    DB_HOST = 'localhost'
    DB_USER = 'app_mavapa'
    DB_PASS = '1234567890'
