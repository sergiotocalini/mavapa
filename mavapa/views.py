#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import md5
from functools import wraps, update_wrapper
import os
# import datetime
import urllib
import requests
import arrow
import pony
from flask import Flask, request, render_template, g, jsonify, current_app
from flask import url_for, abort, flash, redirect, session, make_response
from pony.orm import select, count, commit, desc
from .forms import Login, Reset
# from .lib import *
from .lib.models import db, db_session
from .lib.models import App, Token, User, Backend, Session, Retrieve
from .lib.models import NotifyAgent
from .lib.backends import LDAP
from .mavapa_server import mavapa_server
from datetime import datetime, timedelta

app = Flask(__name__, instance_relative_config=False)
app.config.from_object(os.environ.get('APP_SETTINGS', None))
app.register_blueprint(mavapa_server)

context = app.config.get('APPLICATION_ROOT', '')
if 'CDN_LOCAL' not in app.config:
    app.config['CDN_LOCAL'] = '%s/static/app' % context

if 'CDN_EXTRAS' not in app.config:
    app.config['CDN_EXTRAS'] = '%s/static/extras' % context

if 'CDN_MAVAPA' not in app.config:
    app.config['CDN_MAVAPA'] = '%s/static' % context

if app.config['DB_TYPE'] == 'mysql':
    db.bind(
        provider=app.config['DB_TYPE'], host=app.config['DB_HOST'],
        port=app.config['DB_PORT'], db=app.config['DB_NAME'],
        user=app.config['DB_USER'], passwd=app.config['DB_PASS']
    )
else:
    exit(0)

db.generate_mapping(create_tables=True)
pony.orm.sql_debug(app.config['DB_DEBUG'])


def get_from_backend(**kwargs):
    qfilter = dict((x, kwargs[x]) for x in kwargs if x in ['id', 'email'])
    if qfilter:
        account = get_data('User', **qfilter)
        if account:
            uinfo = {
                'lastname': account.lastname,
                'firstname': account.firstname,
                'avatar': account.avatar(),
                'mobile': account.mobile,
                'mail': account.email
            }
            if not account.backend:
                return uinfo
            else:
                backend = account.backend.to_dict()
                provider = LDAP(**backend)
                qfilter = '(&(%s=%s)%s)' % (
                    backend['login'], account.email,
                    backend['filter']
                )
                only = [
                    'description', 'title', 'idNumber', 'birthDate',
                    'postalAddress', 'o', 'ou', 'telephoneNumber'
                ]
                query = provider.query(filter=qfilter, attrs=only,
                                       basedn=backend['basedn'], limit=1)
                for attr in only:
                    if attr in query[0][1]:
                        uinfo[attr] = query[0][1][attr][0]
                return uinfo
    return None


# @db_session(retry=3)
def get_data(table, **kwargs):
    if kwargs:
        return eval(table).get(**kwargs)
    else:
        return select(o for o in eval(table))


@app.context_processor
def custom_tools():
    def time_age(datetime, endword='years'):
        born = arrow.get(datetime)
        today = arrow.now()
        year = today.year - born.year
        age = year - ((today.month, today.day) < (born.month, born.day))
        return '%i %s' % (age, endword)

    def time_generalize(datetime, fmt='MMMM D, YYYY'):
        local = arrow.get(datetime, 'YYYYMMDDHHmmss')
        return local.format(fmt)

    def time_humanize(dt):
        dtutc = datetime.utcfromtimestamp(float(dt.strftime('%s')))
        local = arrow.Arrow.fromdatetime(dtutc)
        return local.humanize()

    def encrypt_email(email):
        tmp = email.split('@')
        stremail = email[0:3]
        stremail += ''.join(['x' for i in xrange(len(tmp[0]) - 3)])
        stremail += "@" + tmp[1]
        return stremail

    def encrypt_telephone(number, last=4):
        show = number[0:3]
        show += ''.join(['x' for i in xrange(len(number) - last - 3)])
        show += number[len(number) - last:len(number)]
        return show

    return dict(data=get_data, ago=time_humanize, timez=time_generalize,
                age=time_age, encrypt_email=encrypt_email,
                encrypt_telephone=encrypt_telephone)


@db_session(retry=3)
def backends_search_users(email, passwd=None, exist=False):
    users = []
    for i in select(o for o in Backend):
        if i.type in ['LDAP', 'AD']:
            qfilter = '(&(%s=%s)%s)' % (i.login, email, i.filter)
            attrs = ['givenname', 'sn', 'mail', 'mobile', 'mailRecovery']
            oa = LDAP(**i.to_dict(only=['host', 'port', 'binddn', 'bindpw']))
            query = oa.query(filter=qfilter, attrs=attrs,
                             basedn=i.basedn, limit=1)
            if query:
                for dn, x in query:
                    email = x['mail'][0].encode('utf-8').lower()
                    ondb = get_data('User', email=email)
                    if not exist and ondb:
                        continue
                    fname = x['givenName'][0].decode('utf-8').title()
                    lname = x['sn'][0].decode('utf-8').title()
                    info = {}
                    info['email'] = x['mail'][0].encode('utf-8').lower()
                    info['backend'] = i.to_dict(only=['id', 'name', 'type'])
                    info['firstname'] = fname
                    info['lastname'] = lname
                    info['mobile'] = ''
                    info['mailrecovery'] = ''
                    info['exist'] = True if ondb else False
                    if 'mobile' in x:
                        mobile = x['mobile'][0].decode('utf-8')
                        info['mobile'] = mobile
                    if 'mailRecovery' in x:
                        recover = x['mailRecovery'][0].decode('utf-8')
                        info['mailrecovery'] = recover
                    users.append(info)
    return users


@db_session(retry=3)
def session_create(account):
    sid = Session(user=get_data('User', id=account), status=True,
                  agent_address=request.access_route[0],
                  agent_string=request.user_agent.string,
                  agent_platform=request.user_agent.platform,
                  agent_browser=request.user_agent.browser,
                  agent_version=request.user_agent.version)
    commit()
    return sid.to_dict()


@db_session(retry=3)
def session_destroy():
    mavapa_session = session.get('mavapa_session', None)
    if mavapa_session:
        msid = get_data('Session', id=mavapa_session)
        if msid:
            expired_on = datetime.now()
            msid.expired_on = expired_on
            msid.status = False
            for token in select(t for t in Token if t.session == msid):
                token.expired_on = expired_on
                token.status = False
            commit()
    session.pop('mavapa_session', None)
    session.pop('mavapa_account', None)
    session.pop('mavapa_expired', None)


@db_session(retry=3)
def user_onfly(user, passwd):
    for i in select(o for o in Backend if o.onfly):
        if i.type in ['LDAP', 'AD']:
            qfilter = '(&(%s=%s)%s)' % (i.login, user, i.filter)
            attrs = ['givenname', 'sn', 'mail', 'mobile', 'mailRecovery']
            oa = LDAP(**i.to_dict(only=['host', 'port', 'binddn', 'bindpw']))
            query = oa.query(filter=qfilter, attrs=attrs,
                             basedn=i.basedn, limit=1)
            if query:
                if oa.auth(query[0][0], passwd):
                    match = get_data('User', email=query[0][1]['mail'][0])
                    if not match:
                        fname = query[0][1]['givenName'][0].decode('utf-8')
                        lname = query[0][1]['sn'][0].decode('utf-8')
                        info = {'email': user.decode('utf-8'), 'backend': i,
                                'firstname': fname.title(),
                                'lastname': lname.title()}
                        if 'mobile' in query[0][1]:
                            mobile = query[0][1]['mobile'][0].decode('utf-8')
                            info['mobile'] = mobile

                        if 'mailRecovery' in query[0][1]:
                            recover = query[0][1]['mailRecovery'][0]
                            info['mailrecovery'] = recover.decode('utf-8')

                        account = User(**info)
                        commit()
                        return account
                    else:
                        return match
    return False


@db_session(retry=3)
def user_login(user, passwd):
    account = get_data('User', email=user)
    attrs = ['givenName', 'sn', 'mobile', 'mailRecovery']
    if account:
        if not account.backend:
            passwd_md5 = md5(passwd).hexdigest()
            if account.passwd == passwd_md5:
                return account
        elif account.backend.type in ['LDAP', 'AD']:
            provider = LDAP(host=account.backend.host,
                            port=account.backend.port,
                            binddn=account.backend.binddn,
                            bindpw=account.backend.bindpw)

            qfilter = '(&(%s=%s)%s)' % (
                account.backend.login, user,
                account.backend.filter
            )
            query = provider.query(filter=qfilter, attrs=attrs,
                                   basedn=account.backend.basedn, limit=1)
            if query:
                if provider.auth(query[0][0], passwd):
                    fname = query[0][1]['givenName'][0].decode('utf-8')
                    lname = query[0][1]['sn'][0].decode('utf-8')
                    update = {'firstname': fname.title(),
                              'lastname': lname.title()}
                    if 'mobile' in query[0][1]:
                        mobile = query[0][1]['mobile'][0].decode('utf-8')
                        update['mobile'] = mobile

                    if 'mailRecovery' in query[0][1]:
                        recover = query[0][1]['mailRecovery'][0]
                        update['mailrecovery'] = recover.decode('utf-8')

                    account.set(**update)
                    commit()
                    return account
    else:
        return user_onfly(user, passwd)
    return False


@db_session(retry=3)
def user_changepwd(user, passwd):
    account = get_data('User', email=user)
    if account:
        if not account.backend:
            account.passwd = md5(passwd).hexdigest()
            commit()
        elif account.backend.type in ['LDAP', 'AD']:
            backend = account.backend.to_dict()
            provider = LDAP(**backend)

            qfilter = '(&(%s=%s)%s)' % (
                backend['login'], user,
                backend['filter']
            )
            query = provider.query(filter=qfilter, attrs=['userPassword'],
                                   basedn=backend['basedn'], limit=1)
            if query:
                if backend['type'] == 'LDAP':
                    newpwd = provider.make_secret(passwd)
                else:
                    n = ('"', passwd, '"')
                    newpwd = ''.join(n).encode('utf-16').lstrip('\377\376')
                provider.modify(query[0][0],
                                {'unicodePwd': newpwd},
                                {'unicodePwd': '*'})
    return False


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def login_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if not session.get('mavapa_account'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_func


def admin_required(f):
    @wraps(f)
    @db_session(retry=3)
    def decorated_func(*args, **kwargs):
        if not g.user.admin:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_func


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            if 'admin' not in roles:
                return redirect(url_for('index', next=request.url))
            return f(*args, **kwargs)
        return decorated_func
    return decorator


def is_admin():
    return g.user.admin


@app.before_request
@db_session(retry=3)
def before_request():
    mavapa_session = session.get('mavapa_session', None)
    mavapa_account = session.get('mavapa_account', None)
    mavapa_expired = session.get('mavapa_expired', None)
    if mavapa_session and (mavapa_expired > datetime.now()):
        if mavapa_account:
            g.user = get_data('User', email=mavapa_account)
            if g.user:
                g.user.last_seen = datetime.now()
                commit()
    else:
        if mavapa_session:
            expire = get_data('Session', id=mavapa_session)
            if expire:
                expire.delete()
                commit()
        redirect(url_for('logout'))


@app.route('/')
@app.route('/index')
@login_required
@db_session(retry=3)
def index():
    return render_template('index.html')


@app.route('/admin', defaults={'mod': 'dash'})
@app.route('/admin/<mod>')
@login_required
@admin_required
@db_session(retry=3)
def admin(mod):
    if mod == 'users':
        return render_template('admin/users/index.html')
    elif mod == "applications":
        return render_template('admin/applications/index.html')
    elif mod == "notifications":
        return render_template('admin/notifications/index.html')
    elif mod == "organizations":
        return render_template('admin/organizations/index.html')
    elif mod == "security":
        return render_template('admin/security/index.html')
    else:
        return render_template('admin/index.html')


@app.route('/apps')
@login_required
@db_session(retry=3)
def apps():
    apps = {}
    for i in get_data('App'):
        if i.hidden is True:
            continue
        tag = 'General'
        if i.tags:
            tag = i.tags
        if tag not in apps:
            apps[tag] = []
        apps[tag].append(i)
    return render_template('apps.html', apps_list=apps)


@app.route('/developers')
def developers():
    return render_template('developers.html')


@app.route('/favicon.ico')
def favicon():
    return redirect("%s/img/favicon.ico" % app.config['CDN_MAVAPA'])


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('mavapa_session'):
        form = Login(request.form)
        if request.method == 'POST' and form.validate():
            account = user_login(request.form['email'],
                                 request.form['password'])
            if account is False:
                flash('Username or Password is invalid', 'error')
                return render_template('login.html', form=form)
            else:
                new_session = session_create(account.id)
                session['mavapa_session'] = new_session['id']
                session['mavapa_expired'] = new_session['expired_on']
                session['mavapa_account'] = account.email
                next_url = session.pop('next_url', None)
                if next_url is None:
                    next_url = request.args.get("next")
                    if next_url is None:
                        next_url = url_for('index')
                return redirect(urllib.parse.unquote(next_url))
        return render_template('login.html', form=form)
    else:
        next_url = session.pop('next_url', None)
        if next_url is None:
            next_url = request.args.get("next")
            if next_url is None:
                next_url = url_for('index')
        return redirect(urllib.parse.unquote(next_url))


@app.route('/logout')
@db_session(retry=3)
def logout():
    session_destroy()
    return redirect(request.args.get("next") or url_for('login'))


@app.route('/profile', defaults={'userid': 'me'})
@app.route('/profile/<userid>')
@login_required
@db_session(retry=3)
def profile(userid):
    if userid == 'me':
        qfilter = {'email': session['mavapa_account']}
    else:
        qfilter = {'id': userid}
    account = get_from_backend(**qfilter)
    return render_template('profile.html', account=account)


@app.route('/register')
def register():
    if not session.get('mavapa_session'):
        return render_template('register.html', method=2)
    else:
        return redirect(url_for('index'))


@app.route('/reset', methods=['GET', 'POST'])
@db_session(retry=3)
def reset():
    form = Reset(request.form)
    account = None
    change = None
    if request.method == 'POST' and form.validate():
        account = get_data('User', email=form.email.data)
        if any(True for i in ['submit', 'change'] if i in request.form):
            token = get_data('Retrieve', user=account.id, code=form.code.data)
            if token:
                if 'submit' in request.form:
                    change = True
                else:
                    user_changepwd(account.email, form.passwd.data)
                    token.used_on = datetime.now()
                    commit()
                    return redirect(url_for('login'))
            else:
                flash('Error code', 'danger')
    return render_template('reset.html', form=form,
                           user=account, reset=change)


@app.route('/support')
def support():
    return render_template('index.html')


@app.route('/api/apps', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@db_session(retry=3)
def api_apps():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in ['id', 'name'] if args.get(x))
    if request.method == 'GET':
        if not args.get('id', False):
            if not session.get('mavapa_account'):
                abort(403)
            only = ['created_at', 'desc', 'icon', 'name', 'tags', 'url']
            apps_all = []
            fav = []
            apps = get_data('App')
            if apps:
                apps_all = [i.to_dict(only) for i in apps if i.hidden is False]

            if args.get('favorites', False):
                user = get_data('User', email=session['mavapa_account'])
                fav = [i.to_dict(only) for i in user.apps if not i.hidden]

            data = []
            keys = {}
            for x in fav + apps_all:
                if keys.get(x['name'], None):
                    continue
                data.append(x)
                keys[x["name"]] = 1
            return jsonify(datetime=datetime.now(), apps=data[:12])
        else:
            app = get_data('App', id=args['id'])
            if app and is_admin():
                return jsonify(datetime=datetime.now(), data=[app.to_dict()])
    elif request.method == 'POST':
        content = request.get_json(silent=True)
        if qfilter:
            app = get_data('App', **qfilter)
            if app:
                app.set(**content)
            else:
                App(**content)
        else:
            App(**content)
        commit()
    elif request.method == 'DELETE':
        if qfilter:
            app = get_data('App', **qfilter)
            if app:
                app.delete()
                commit()
            else:
                abort(404)
    return jsonify(datetime=datetime.now())


@app.route('/api/notify/code', methods=['POST'])
@db_session(retry=3)
def api_code():
    content = request.get_json(silent=True)
    if content:
        if 'account' in content:
            user = get_data('User', email=content['account'])
            if user:
                send = True
                token = get_data('Retrieve', user=user.id)
                if token:
                    if token.used_on or token.expired_on <= datetime.now():
                        token.delete()
                        token = Retrieve(user=user, methods=content['type'])
                else:
                    token = Retrieve(user=user, methods=content['type'])

                if content['type'] not in token.methods.split(','):
                    methods = [x for x in token.methods.split(',') if x]
                    token.methods = ','.join(methods + [content['type']])
                else:
                    send = False
                commit()

                NOTIFY_API = get_data('Config', key='NOTIFY_API')
                if NOTIFY_API and send:
                    URL = NOTIFY_API.value
                    NOTIFY_TOKEN = get_data('Config', key='NOTIFY_TOKEN')
                    if NOTIFY_TOKEN:
                        URL += '?token=%s' % NOTIFY_TOKEN.value
                    if content['type'] == 'sms':
                        text = "Your account verification code is {code}."
                        content['number'] = user.mobile.replace('-', '')
                        content['text'] = text.format(code=token.code)
                    elif content['type'] == 'email':
                        content['to'] = user.mailrecovery
                        content['subject'] = """
                        Mavapa: Verification Code
                        """
                        content['body'] = """
                        Code: %s
                        """ % token.code
                    requests.post(URL, json=content, verify=False)
                else:
                    print(user.email, token.code)
    return jsonify(datetime=datetime.now())


@app.route('/api/notify/agents', methods=['GET', 'POST', 'DELETE'])
@db_session(retry=3)
def api_notify_agents():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'name'])
    if qfilter:
        agent = get_data('NotifyAgent', **qfilter)
        if request.method == 'GET':
            if agent:
                data = agent.to_dict()
                return jsonify(datetime=datetime.now(), data=[data])
        elif request.method == 'DELETE':
            if session.get('account') and is_admin():
                if agent:
                    agent.delete()
                    commit()
        else:
            if session.get('account') and is_admin():
                content = request.get_json(silent=True)
                if content and agent:
                    agent.set(**content)
                    commit()
                elif content:
                    NotifyAgent(**content)
                    commit()
    return jsonify(datetime=datetime.now())


@app.route('/api/backends', methods=['GET', 'POST', 'DELETE'])
@db_session(retry=3)
def api_backends():
    only = ['name', 'type', 'id']
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in only and args[x])
    if qfilter:
        backends = [get_data('Backend', **qfilter)]

    if request.method == 'GET':
        if not qfilter:
            backends = get_data('Backend')

        if is_admin():
            data = [i.to_dict() for i in backends]
        else:
            data = [i.to_dict(only) for i in get_data('Backend')]
        return jsonify(datetime=datetime.now(), backends=data)
    elif request.method == 'DELETE':
        if qfilter and is_admin():
            for b in backends:
                b.delete()
            commit()
        else:
            abort(403)
    else:
        content = request.get_json(silent=True)
        if content and is_admin():
            if not qfilter:
                Backend(**content)
            else:
                backends[0].set(**content)
            commit()
    return jsonify(datetime=datetime.now())


@app.route('/api/backends/tree', methods=['GET'])
@db_session(retry=3)
def api_backends_tree():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['backend', 'type'])
    qfilter.setdefault('type', 'items')
    data = []
    if qfilter['type'] == 'items':
        basedn = '{0}'
        attrs = ['dn']
        scope = 2
    elif qfilter['type'] == 'schemas':
        basedn = 'cn=subschema'
        attrs = ['*', '+']
        scope = 0
    else:
        abort(404)

    if qfilter['backend']:
        backend = filter(None, [get_data('Backend', id=qfilter['backend'])])
    else:
        backend = get_data('Backend')
    for i in backend:
        if i.type in ['LDAP', 'AD']:
            oa = LDAP(**i.to_dict(only=['host', 'port', 'binddn', 'bindpw']))
            data = oa.tree(
                attrs=attrs,
                basedn=basedn.format(i.basedn),
                scope=scope
            )
    return jsonify(datetime=datetime.now(), data=data, title=qfilter)


@app.route('/api/backends/items', methods=['GET', 'POST', 'PUT', 'DELETE'])
@db_session(retry=3)
def api_backends_items():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['backend', 'dn'])
    only_conn = ['host', 'port', 'binddn', 'bindpw']
    data = []
    if 'backend' in qfilter or 'dn' in qfilter:
        for i in [get_data('Backend', id=qfilter['backend'])]:
            if i.type in ['LDAP', 'AD']:
                oa = LDAP(**i.to_dict(only=only_conn))
                query = oa.query(
                    filter=qfilter['dn'], attrs=['*'],
                    basedn=i.basedn, limit=1, scope=0, dn=True
                )

                if request.method == 'GET':
                    data = query
                elif request.method == 'PUT':
                    for q in query:
                        attrs_new = {}
                        attrs_old = {}
                        content = request.get_json(silent=True)
                        for attr in content:
                            if content[attr] != q[1].get(attr, [''])[0]:
                                attrs_old[attr] = q[1].get(attr, ['*'])[0]
                                attrs_new[attr] = content[attr]
                        oa.modify(q[0], attrs_new, attrs_old)
                        data.append((q[0], attrs_new, attrs_old))
                    break
    return jsonify(datetime=datetime.now(), data=data)


@app.route('/api/backends/search', methods=['GET'])
@db_session(retry=3)
def api_backends_search():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args)
    qfilter.setdefault('backend', None)
    qfilter.setdefault('exclude', '')
    only_conn = ['host', 'port', 'binddn', 'bindpw']
    only_backend = ['id', 'name', 'type', 'desc']
    data = []
    if 'filter' in qfilter:
        if qfilter['backend']:
            backend = filter(
                None, [get_data('Backend', id=qfilter['backend'])]
            )
        else:
            backend = get_data('Backend')
        qfilter['exclude'] = qfilter['exclude'].split(',')
        for i in backend:
            conn = i.to_dict(only=only_backend)
            if i.type in ['LDAP', 'AD']:
                oa = LDAP(**i.to_dict(only=only_conn))
                query = oa.query(
                    filter=qfilter['filter'],
                    basedn=i.basedn,
                    exclude=qfilter['exclude']
                )
                for row in query:
                    row[1]['backend'] = conn
                    data.append(row)
    return jsonify(datetime=datetime.now(), data=data)


@app.route('/api/backends/search/users', methods=['GET'])
@db_session(retry=3)
def api_backends_search_users():
    args = request.args.to_dict()
    required = ['email', 'filter', 'only', 'backend']
    qfilter = dict((x, args[x]) for x in args if x in required)
    qfilter.setdefault('email', '*')
    qfilter.setdefault('filter', '(ObjectClass=person)')
    qfilter.setdefault('only', 'all')
    qfilter.setdefault('include', '*')
    qfilter.setdefault('exclude', 'jpegPhoto,photo')
    qfilter.setdefault('backend', None)
    data = []
    qfilter['include'] = qfilter['include'].split(',')
    qfilter['exclude'] = qfilter['exclude'].split(',')
    if qfilter['backend']:
        backend = filter(None, [get_data('Backend', id=qfilter['backend'])])
    else:
        backend = get_data('Backend')
    for i in backend:
        conn = i.to_dict(only=['id', 'name', 'type', 'desc'])
        if i.type in ['LDAP', 'AD']:
            oa = LDAP(**i.to_dict(only=['host', 'port', 'binddn', 'bindpw']))
            query = oa.query(
                filter='(&(%s=%s)%s)' % (
                    i.login, qfilter['email'], qfilter['filter']
                ),
                attrs=qfilter['include'], exclude=qfilter['exclude'],
                basedn=i.basedn, limit=1,
            )
            for row in query:
                row[1]['exist'] = False
                if get_data('User', email=row[1]['mail'][0]):
                    row[1]['exist'] = True
                if qfilter['only'] not in ['all', 'ALL']:
                    if qfilter['only'] == 'exist' and not row[1]['exist']:
                        continue
                    elif qfilter['only'] == 'noexist' and row[1]['exist']:
                        continue
                row[1]['backend'] = conn
                data.append(row)

            # if query:
            #     for dn, x in query:
            #         info = {}
            #         info['exist'] = False
            #         if get_data('User', email=x['mail'][0]):
            #             info['exist'] = True
            #         if qfilter['only'] not in ['all', 'ALL']:
            #             if qfilter['only'] == 'exist' and not info['exist']:
            #                 continue
            #             elif qfilter['only'] == 'noexist' and info['exist']:
            #                 continue
            #         info['backend'] = i.to_dict(
            #             only=['id', 'name', 'type', 'desc']
            #         )
            #         for attr in x:
            #             info[attr] = [e.decode('utf-8') for e in x[attr] if attr not in qfilter['exclude'].split(',')]
            #         data.append(info)
    return jsonify(datetime=datetime.now(), data=data)


@app.route('/api/configs/locales', methods=['GET'])
@db_session(retry=3)
def api_configs_locales():
    return jsonify(datetime=datetime.now())


@app.route('/api/configs/timezones', methods=['GET'])
@db_session(retry=3)
def api_configs_timezones():
    return jsonify(datetime=datetime.now())


@app.route('/api/users', methods=['GET', 'POST'])
@db_session(retry=3)
def api_users():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
    only_backend = ['id', 'name', 'type', 'desc']
    if qfilter:
        user = get_data('User', **qfilter)
        if request.method == 'GET':
            if user:
                if session.get('mavapa_session'):
                    data = user.to_dict(exclude=['passwd'])
                    data['backend'] = user.backend.to_dict(only=only_backend) if user.backend else False
                else:
                    only = ['id', 'email', 'firstname', 'lastname']
                    data = user.to_dict(only)
                data['displayname'] = user.displayname
                data['avatar'] = user.avatar()
                return jsonify(datetime=datetime.now(), users=[data])
        else:
            if session.get('mavapa_account') and is_admin():
                content = request.get_json(silent=True)
                if content:
                    if 'backend' in content:
                        if content['backend'] == '0':
                            content['backend'] = None
                if user:
                    user.set(**content)
                else:
                    User(**content)
                commit()
    return jsonify(datetime=datetime.now())


@app.route('/api/users/all', methods=['GET'])
@db_session(retry=3)
def api_users_all():
    args = request.args.to_dict()
    args.setdefault('type', None)
    args.setdefault('filter', None)
    args.setdefault('sort', 'name')
    args.setdefault('order', 'asc')
    args.setdefault('search', None)
    args.setdefault('offset', 0)
    args.setdefault('limit', 50)
    args.setdefault('status', None)
    # only_user = [
    #     'id', 'userid', 'displayname', 'email', 'avatar',
    #     'status', 'title', 'created_on', 'last_seen'
    # ]
    only_backend = ['id', 'name', 'type', 'desc']
    data = []
    raw = get_data('User')

    if args['search']:
        raw = raw.filter(
            lambda o: args['search'].lower() in o.firstname.lower()
            or
            args['search'].lower() in o.lastname.lower()
        )

    if args['status']:
        raw = raw.filter(lambda o: args['status'] == o.status)

    if args['sort'] == 'displayname':
        args['sort'] = 'lastname'

    if getattr(User, args['sort'], None):
        if args['order'] == 'desc':
            raw = raw.order_by(lambda o: desc(getattr(o, args['sort'])))
        else:
            raw = raw.order_by(lambda o: getattr(o, args['sort']))

    total = count(raw)
    if args['limit'] not in ["no", "false", "f", "-1", "None"]:
        raw = raw.limit(int(args['limit']), offset=int(args['offset']))

    for i in raw:
        row = i.to_dict(related_objects=False)
        row['displayname'] = i.displayname
        row['avatar'] = i.avatar()
        row['backend'] = i.backend.to_dict(only=only_backend) if i.backend else False
        # if args['filter'] != 'team' and i.team:
        #     team = i.team.to_dict(only_team)
        #     team['manager'] = i.team.manager.to_dict(only_user)
        #     row['team'] = team
        data.append(row)
    return jsonify(datetime=datetime.now(), data=data, total=total)


@app.route('/api/users/search', methods=['GET'])
@db_session(retry=3)
def api_users_search():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
    only_backend = ['id', 'name', 'type', 'desc']
    data = []
    if qfilter:
        res = filter(None, [get_data('User', **qfilter)])
    else:
        res = get_data('User')

    for i in res:
        user = i.to_dict(exclude=['passwd'])
        if i.backend:
            user['backend'] = i.backend.to_dict(only=only_backend)
        user['displayname'] = i.displayname
        user['avatar'] = i.avatar()
        data.append(user)
    return jsonify(datetime=datetime.now(), data=data)


if __name__ == "__main__":
    app.run('0.0.0.0', 7001)
