#!/usr/bin/env python
import os
import sys

APP_NAME = 'mavapa'
APP_VERS = '0.0.1'
APP_DESC = 'Accounts Management.'
APP_SITE = 'https://github.com/sergiotocalini/mavapa'
APP_PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

if not (APP_PATH in sys.path):
    sys.path.insert(0, APP_PATH)
