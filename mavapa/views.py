#!/usr/bin/env python
import os
from hashlib import md5
import datetime
import arrow
import requests
import urllib
import json
import string
import random
from functools import wraps
#from werkzeug.datastructures import CallbackDict
from flask import Flask, request, render_template, g, jsonify
from flask import url_for, abort, flash, redirect, session
#from flask.sessions import SessionInterface, SessionMixin
from forms import *
from lib import *
from mavapa_server import mavapa_server

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(os.environ['APP_SETTINGS'])


if not app.config.has_key('CDN_LOCAL'):
    app.config['CDN_LOCAL'] = '%s/static/app' %app.config.get('APPLICATION_ROOT', '')

if not app.config.has_key('CDN_EXTRAS'):
    app.config['CDN_EXTRAS'] = '%s/static/extras' %app.config.get('APPLICATION_ROOT', '')
    
if not app.config.has_key('CDN_MAVAPA'):
    app.config['CDN_MAVAPA'] = '%s/static' %(app.config.get('APPLICATION_ROOT', ''))

if app.config['DB_TYPE'] == 'mysql':
    db.bind(app.config['DB_TYPE'], host=app.config['DB_HOST'],
            port=app.config['DB_PORT'], db=app.config['DB_NAME'],
            user=app.config['DB_USER'], passwd=app.config['DB_PASS'])
    db.generate_mapping(create_tables=True)
else:
    print('Database doesn\'t tested')
    exit(0)
app.register_blueprint(mavapa_server)
sql_debug(app.config['DB_DEBUG'])

def get_from_backend(**kwargs):
    qfilter = dict((x, kwargs[x]) for x in kwargs if x in ['id', 'email'])
    if qfilter:
        account = get_data('User', **qfilter)
        if account:
            uinfo= {'lastname': account.lastname,
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
                qfilter = '(&(%s=%s)%s)' %(backend['login'], account.email,
                                           backend['filter'])
                only=['description', 'title', 'idNumber', 'birthDate',
                      'postalAddress', 'o', 'ou', 'telephoneNumber']
                query = provider.query(filter=qfilter, attrs=only,
                                       basedn=backend['basedn'], limit=1)
                if query[0][1].has_key('description'):
                    uinfo['description'] = query[0][1]['description'][0]
                if query[0][1].has_key('title'):                
                    uinfo['title'] = query[0][1]['title'][0]
                if query[0][1].has_key('idNumber'):
                    uinfo['idNumber'] = query[0][1]['idNumber'][0]
                if query[0][1].has_key('birthDate'):
                    uinfo['birthDate'] = query[0][1]['birthDate'][0]
                if query[0][1].has_key('o'):
                    uinfo['company'] = query[0][1]['o'][0]
                if query[0][1].has_key('ou'):
                    uinfo['department'] = query[0][1]['ou'][0]
                if query[0][1].has_key('telephoneNumber'):
                    uinfo['telephoneNumber'] = query[0][1]['telephoneNumber'][0]
                return uinfo
    return None

@db_session
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
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return '%i %s' %(age,endword)
        
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
        show  = number[0:3]
        show += ''.join(['x' for i in xrange(len(number) - last - 3)])
        show += number[len(number) - last:len(number)]
        return show

    return dict(data=get_data, ago=time_humanize, timez=time_generalize,
                age=time_age, encrypt_email=encrypt_email,
                encrypt_telephone=encrypt_telephone)

@db_session
def backends_search_users(email, passwd=None, exist=False):
    users = []
    for i in select(o for o in Backend):
        if i.type in ['LDAP', 'AD']:
            qfilter = '(&(%s=%s)%s)' %(i.login, email, i.filter)
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
                    if x.has_key('mobile'):
                        mobile = x['mobile'][0].decode('utf-8')
                        info['mobile'] = mobile
                    if x.has_key('mailRecovery'):
                        recover = x['mailRecovery'][0].decode('utf-8')
                        info['mailrecovery'] = recover
                    users.append(info)
    return users

@db_session
def session_create(account):
    sid = Session(user=get_data('User', id=account), status=True,
                  agent_address=request.access_route[0],
                  agent_string=request.user_agent.string,
                  agent_platform=request.user_agent.platform,
                  agent_browser=request.user_agent.browser,
                  agent_version=request.user_agent.version)
    commit()
    return sid.to_dict()

@db_session
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

@db_session
def user_onfly(user, passwd):
    for i in select(o for o in Backend if o.onfly == True):
        if i.type in ['LDAP', 'AD']:
            qfilter = '(&(%s=%s)%s)' %(i.login, user, i.filter)
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
                        info = {'email': user.decode('utf-8'), 'backend':i,
                                'firstname':fname.title(),
                                'lastname':lname.title()}
                        if query[0][1].has_key('mobile'):
                            mobile = query[0][1]['mobile'][0].decode('utf-8')
                            info['mobile'] = mobile

                        if query[0][1].has_key('mailRecovery'):
                            recover = query[0][1]['mailRecovery'][0]
                            info['mailrecovery'] = recover.decode('utf-8')
                            
                        account = User(**info)
                        commit()
                        return account
                    else:
                        return match
    return False

@db_session
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

            qfilter = '(&(%s=%s)%s)' %(account.backend.login, user,
                                       account.backend.filter)
            query = provider.query(filter=qfilter, attrs=attrs,
                                   basedn=account.backend.basedn, limit=1)
            if query:
                if provider.auth(query[0][0], passwd):
                    fname = query[0][1]['givenName'][0].decode('utf-8')
                    lname = query[0][1]['sn'][0].decode('utf-8')
                    update = {'firstname': fname.title(),
                              'lastname': lname.title()}
                    if query[0][1].has_key('mobile'):
                        mobile = query[0][1]['mobile'][0].decode('utf-8')
                        update['mobile'] = mobile
                        
                    if query[0][1].has_key('mailRecovery'):
                        recover = query[0][1]['mailRecovery'][0]
                        update['mailrecovery'] = recover.decode('utf-8')

                    account.set(**update)
                    commit()
                    return account
    else:
        return user_onfly(user, passwd)
    return False

@db_session
def user_changepwd(user, passwd):
    account = get_data('User', email=user)
    if account:
        if not account.backend:
            account.passwd = md5(passwd).hexdigest()
            commit()
        elif account.backend.type in ['LDAP', 'AD']:
            backend = account.backend.to_dict()
            provider = LDAP(**backend)

            qfilter = '(&(%s=%s)%s)' %(backend['login'], user,
                                       backend['filter'])
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
                                {'unicodePwd':'*'})
    return False

def login_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if not session.get('mavapa_account'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_func

def admin_required(f):
    @wraps(f)
    @db_session    
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
@db_session
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
@db_session
def index():
    print(request.remote_addr, request.access_route)
    return render_template('index.html')

@app.route('/admin', defaults={'mod': 'dash'})
@app.route('/admin/<mod>')
@login_required
@admin_required
@db_session
def admin(mod):
    if mod == 'users':
        return render_template('admin/users/index.html')
    elif mod == "apps":
        return render_template('admin_apps.html')
    elif mod == "notify":
        return render_template('admin_notify.html')
    else:
        return render_template('admin_dash.html')

@app.route('/apps')
@login_required
@db_session
def apps():
    apps = {}
    for i in get_data('App'):
        if i.hidden == True:
            continue
        tag = 'General'
        if i.tags:
            tag  = i.tags
        if tag not in apps:
          apps[tag] = []
        apps[tag].append(i)
    return render_template('apps.html', apps_list=apps)
    
@app.route('/developers')
def developers():
    return redirect('http://developers.corpam.com.ar/')

@app.route('/favicon.ico')
def favicon():
    return redirect("%s/img/favicon.ico" %app.config['CDN_MAVAPA'])

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
                return redirect(urllib.unquote(next_url))
        return render_template('login.html', form=form)
    else:
        next_url = session.pop('next_url', None)
        if next_url is None:
            next_url = request.args.get("next")
            if next_url is None:
                next_url = url_for('index')
        return redirect(urllib.unquote(next_url))

@app.route('/logout')
@db_session
def logout():
    session_destroy()
    return redirect(request.args.get("next") or url_for('login'))

@app.route('/api/notify/code', methods=['POST'])
@db_session
def api_code():
    content = request.get_json(silent=True)
    if content:
        if content.has_key('account'):
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

                if not content['type'] in token.methods.split(','):
                    methods = [x for x in token.methods.split(',') if x]
                    token.methods = ','.join(methods + [content['type']])
                else:
                    send = False
                commit()
                
                NOTIFY_API = get_data('Config', key='NOTIFY_API')
                if NOTIFY_API:
                    URL = NOTIFY_API.value
                    NOTIFY_TOKEN = get_data('Config', key='NOTIFY_TOKEN')
                    if NOTIFY_TOKEN:
                        URL += '?token=%s' %NOTIFY_TOKEN.value
                    if content['type'] == 'sms':
                        text = "Your account verification code is {code}."
                        content['number'] = user.mobile.replace('-', '')
                        content['text'] =  text.format(code=token.code)
                    elif content['type'] == 'email':
                        content['to'] = user.mailrecovery
                        content['subject'] = """
                        Mavapa: Verification Code
                        """
                        content['body'] = """
                        Code: %s
                        """ %token.code
                    r = requests.post(URL, json=content, verify=False)
                else:
                    print(user.email, token.code)
    return jsonify(datetime=datetime.now())

@app.route('/api/apps', methods=['GET', 'POST', 'DELETE'])
@db_session
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
                apps_all = [i.to_dict(only) for i in apps if i.hidden == False]
                
            if args.get('favorites', False):
                user = get_data('User', email=session['mavapa_account'])
                fav = [i.to_dict(only) for i in user.apps if i.hidden == False]
                
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

@app.route('/api/backends', methods=['GET', 'POST'])
@db_session
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
    else:
        content = request.get_json(silent=True)
        if content and is_admin():
            print(content)
            if not qfilter:
                Backend(**content)
            else:
                backends[0].set(**content)
            commit()
    return jsonify(datetime=datetime.now())


@app.route('/api/notify/agents', methods=['GET', 'POST', 'DELETE'])
@db_session
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


@app.route('/api/users/search', methods=['GET'])
@db_session
def api_users_search():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
    only_backend = ['id', 'name', 'type', 'desc']
    data = []
    if not qfilter:
        for i in get_data('User'):
            user = i.to_dict(exclude=['passwd'])
            user['backend'] = i.backend.to_dict(only=only_backend) if i.backend else None
            user['displayname'] = i.displayname
            user['avatar'] = i.avatar()
            data.append(user)
    else:
        res = get_data('User', **qfilter)
        if res:
            user = res.to_dict(exclude=['passwd'])
            user['backend'] = i.backend.to_dict(only=only_backend) if i.backend else None
            user['displayname'] = res.displayname
            user['avatar'] = res.avatar()
            data.append(user)
    return jsonify(datetime=datetime.now(), data=data)


@app.route('/api/backends/search/users', methods=['GET'])
@db_session
def api_backends_search_users():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['email', 'filter', 'only'])
    qfilter.setdefault('email', '*')
    qfilter.setdefault('filter', '(ObjectClass=person)')
    qfilter.setdefault('only', 'all')
    data = []
    for i in select(o for o in Backend):
        if i.type in ['LDAP', 'AD']:
            oa = LDAP(**i.to_dict(only=['host', 'port', 'binddn', 'bindpw']))
            query = oa.query(
                filter = '(&(%s=%s)%s)' %(i.login, qfilter['email'], qfilter['filter']),
                attrs = ['givenname', 'sn', 'mail', 'mobile', 'mailRecovery'],
                basedn = i.basedn,
                limit = 1
            )
            if query:
                for dn, x in query:
                    info = {}
                    for attr in x:
                        info[attr] = [e.encode('utf-8').lower() for e in x[attr]]
                    info['exist'] = True if get_data('User', email=info['mail'][0]) else False
                    if qfilter['only'] not in ['all', 'ALL']:
                        if qfilter['only'] == 'exist' and not info['exist']:
                            continue
                        elif qfilter['only'] == 'noexist' and info['exist']:
                            continue
                    fname = x['givenName'][0].decode('utf-8').title()
                    lname = x['sn'][0].decode('utf-8').title()
                    info['backend'] = i.to_dict(only=['id', 'name', 'type', 'desc'])
                    info['firstname'] = fname
                    info['lastname'] = lname
                    info['mobile'] = ''
                    info['mailrecovery'] = ''
                    if x.has_key('mobile'):
                        mobile = x['mobile'][0].decode('utf-8')
                        info['mobile'] = mobile
                    if x.has_key('mailRecovery'):
                        recover = x['mailRecovery'][0].decode('utf-8')
                        info['mailrecovery'] = recover
                    data.append(info)
    return jsonify(datetime=datetime.now(), data=data)


@app.route('/api/users', methods=['GET', 'POST'])
@db_session
def api_users():
    args = request.args.to_dict()
    qfilter = dict((x, args[x]) for x in args if x in ['id', 'email'])
    if qfilter:
        user = get_data('User', **qfilter)
        if request.method == 'GET':
            if user:
                if session.get('mavapa_session'):
                    data = user.to_dict(exclude=['passwd'])
                    data['backend'] = user.backend.to_dict(only=['id', 'name', 'type', 'desc'])
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
                    if content.has_key('backend'):
                        if content['backend'] == '0':
                            content['backend'] = None
                if user:
                    user.set(**content)
                else:
                    User(**content)
                commit()
    return jsonify(datetime=datetime.now())


@app.route('/api/users/all', methods=['GET'])
@db_session
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
    only_user = ['id', 'userid', 'displayname', 'email', 'avatar',
                 'status', 'title', 'created_on', 'last_seen']
    only_backend = ['id', 'name', 'type', 'desc']
    data = []
    raw = get_data('User')
        
    if args['search']:
        raw = raw.filter(lambda o: args['search'].lower() in o.firstname.lower() or args['search'].lower() in o.lastname.lower())

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
        row['backend'] = i.backend.to_dict(only=only_backend) if i.backend else None
        # if args['filter'] != 'team' and i.team:
        #     team = i.team.to_dict(only_team)
        #     team['manager'] = i.team.manager.to_dict(only_user)
        #     row['team'] = team
        data.append(row)
    return jsonify(datetime=datetime.now(), data=data, total=total)


@app.route('/profile', defaults={'userid': 'me'})
@app.route('/profile/<userid>')
@login_required
@db_session
def profile(userid):
    if userid == 'me':
        qfilter = {'email': session['mavapa_account']}
    else:
        qfilter = {'id': userid}
    account = get_from_backend(**qfilter)
    return render_template('profile.html', account=account)

@app.route('/reset', methods=['GET', 'POST'])
@db_session
def reset():
    form = Reset(request.form)
    account = None
    change = None
    if request.method == 'POST' and form.validate():
        account = get_data('User', email=form.email.data)
        if any(True for i in ['submit', 'change'] if i in request.form):
            token = get_data('Retrieve',user=account.id,code=form.code.data)
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

if __name__ == "__main__":
    app.run('0.0.0.0', 7001)
