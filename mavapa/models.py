#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import md5

from pony.orm import (Database, Optional, PrimaryKey, Required, Set,
                      db_session, get, unicode)

db = Database()


def make_hash(lenght=24):
    s = string.ascii_letters + string.digits
    r = ''.join([random.choice(s) for x in range(lenght)])
    return r


class Token(db.Entity):
    _table_ = "tokens"
    created_on = Required(
        datetime,
        sql_type='TIMESTAMP',
        default=datetime.now
    )
    expired_on = Required(
        datetime,
        default=lambda: datetime.now() + timedelta(days=30)
    )
    code = Required(unicode)
    access_token = Optional(unicode)
    status = Required(bool, default=True)
    user = Required("User")
    app = Required("App")
    scopes = Set("Scope")
    session = Required('Session')


class User(db.Entity):
    _table_ = "users"
    id = PrimaryKey(unicode, default=lambda: make_hash())
    email = Required(unicode, auto=True)
    passwd = Optional(unicode, nullable=True)
    firstname = Optional(unicode)
    lastname = Optional(unicode)
    dname = Optional(
        unicode, default="{lastname}, {firstname}", column="displayname"
    )
    mobile = Optional(unicode)
    mailrecovery = Optional(unicode)
    status = Required(bool, default=True)
    admin = Required(bool, default=False)
    created_at = Required(datetime, default=datetime.now)
    last_seen = Optional(datetime, default=datetime.now)
    genre = Optional(unicode, nullable=True, default=None)
    lang = Required(unicode, default='Auto')
    timezone = Optional(unicode, nullable=True)
    tokens = Set(Token)
    backend = Optional("Backend")
    apps = Set("App")
    retrieves = Set("Retrieve")
    sessions = Set('Session')

    @property
    @db_session
    def displayname(self):
        return self.dname.format(**self.to_dict())

    @db_session
    def avatar(self, size=256):
        kwargs = {}
        kwargs['size'] = size
        kwargs['cdn'] = get(o for o in Config if o.key == 'CDN_AVATAR')
        kwargs['photo'] = md5(self.email.encode('utf-8')).hexdigest()
        if kwargs['cdn']:
            return '{cdn}/{photo}?s={size}'.format(**kwargs)
        else:
            return '//s.gravatar.com/avatar/{photo}?s={size}'.format(**kwargs)


class Session(db.Entity):
    _table_ = "sessions"
    id = PrimaryKey(unicode, default=lambda: make_hash())
    created_on = Required(
        datetime, sql_type='TIMESTAMP', default=datetime.now
    )
    expired_on = Required(
        datetime, default=lambda: datetime.now() + timedelta(days=30)
    )
    agent_address = Required(unicode)
    agent_string = Optional(unicode)
    agent_platform = Optional(unicode)
    agent_browser = Optional(unicode)
    agent_version = Optional(unicode)
    status = Required(bool, default=True)
    user = Required(User)
    tokens = Set(Token)


class App(db.Entity):
    _table_ = "apps"
    name = Required(unicode, unique=True)
    desc = Optional(unicode, nullable=True)
    url = Required(unicode)
    icon = Required(unicode)
    hidden = Required(bool, default=True)
    client_id = Required(unicode)
    client_secret = Required(unicode)
    redirect_uri = Required(unicode)
    created_at = Required(
        datetime, sql_type='TIMESTAMP', default=datetime.now
    )
    tags = Optional(unicode)
    users = Set(User)
    tokens = Set(Token)
    scopes = Set("Scope")
    notify_profiles = Set('NotifyProfile')


class Backend(db.Entity):
    _table_ = "backends"
    name = Required(unicode, unique=True, nullable=True)
    desc = Optional(unicode)
    type = Required(unicode, default='LOCAL')
    host = Optional(unicode)
    port = Optional(int)
    binddn = Optional(unicode)
    bindpw = Optional(unicode)
    basedn = Optional(unicode)
    filter = Optional(unicode)
    timeout = Optional(int)
    onfly = Required(bool, default=False)
    login = Required(unicode, default='mail')
    last_seen = Optional(datetime, default=datetime.now)
    users = Set(User)


class Scope(db.Entity):
    _table_ = "scopes"
    permissions = Required(Decimal)
    apps = Set(App)
    tokens = Set(Token)


class Config(db.Entity):
    _table_ = "configs"
    key = Required(unicode, unique=True)
    value = Required(unicode)


class Retrieve(db.Entity):
    _table_ = "tokens_retrieves"
    id = PrimaryKey(int, auto=True)
    code = Required(unicode, unique=True, default=lambda: make_hash(8))
    created_on = Required(
        datetime, sql_type='TIMESTAMP', default=datetime.now
    )
    expired_on = Required(
        datetime, default=lambda: datetime.now() + timedelta(hours=1)
    )
    used_on = Optional(datetime, nullable=True)
    methods = Optional(unicode, nullable=True, default='')
    user = Required(User)


class NotifyAgent(db.Entity):
    _table_ = 'notify_agents'
    id = PrimaryKey(unicode, default=lambda: make_hash())
    name = Required(unicode)
    type = Required(unicode)
    host = Required(unicode)
    key = Required(unicode)
    last_seen = Required(datetime, sql_type='TIMESTAMP', default=datetime.now)
    notify_profiles = Set('NotifyProfile')


class NotifyProfile(db.Entity):
    _table_ = 'notify_profiles'
    id = PrimaryKey(unicode, default=lambda: make_hash())
    name = Required(unicode)
    type = Required(unicode)
    policy = Required(unicode)
    notify_agents = Set(NotifyAgent)
    apps = Set(App)
