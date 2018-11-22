#!/usr/bin/env python
#from jinja2 import TemplateNotFound
#import requests
import urllib
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, render_template, abort, redirect, request, jsonify, session, url_for
from lib import *
from forms import *

MAVAPA_URL = ''
AUTH_URL = MAVAPA_URL + '/auth?response_type=code'
TOKEN_URL = MAVAPA_URL + '/token'
USER_INFO_URL = MAVAPA_URL + '/who_im/'
LOGOUT_URL = MAVAPA_URL + '/logout'
mavapa_server = Blueprint('mavapa_server', __name__, template_folder='templates')

def make_rnd_str():
    s = string.letters + string.digits
    r = ''.join([random.choice(s) for x in range(24)])
    return r

@db_session
def get_data(table, **kwargs):
    if kwargs:
        return eval(table).get(**kwargs)
    else:
        return select(o for o in eval(table))

@db_session
def save_code(app, user, code):
    """
    Save code in TokenTable, make the relationship with
    a client_id and a user.
    """
    start = datetime.now()
    end = start + timedelta(days=30)
    token = Token(code=code, user=user.id, app=app.id,
                  created_on=start, expired_on=end,
                  session=session['mavapa_session'])
    commit()
    return token

@mavapa_server.route('/who_im/')
@db_session
def who_im():
    """ get user by TokenTable"""
    tk = request.args.get('token')
    token = get_data('Token', access_token=tk)
    if token:
        if token.status and token.expired_on > datetime.now():
            user = token.user.to_dict()
            user['avatar'] = token.user.avatar()
            user['displayname'] = token.user.displayname
            keys = [
                'id', 'firstname', 'lastname', 'displayname', 'avatar',
                'gender', 'email', 'page', 'profile', 'lang', 'timezone',
                'site'
            ]
            data = {}
            for key in keys:
                data[key] = user.get(key, '')
            return jsonify(data)
    return abort(403)

@mavapa_server.route('/token', methods=['POST'])
@db_session
def token():
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    redirect_uri = urllib.unquote(redirect_uri)
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    data = {"error": "invalid_request"}
    app = get_data(
        'App', client_id=client_id, redirect_uri=redirect_uri, client_secret=client_secret
    )
    if app:
        token = get_data('Token', code=code)
        if token:
            tk = make_rnd_str()
            token.access_token = tk
            commit()
            data = {'access_token': tk}
    return jsonify(data)

@mavapa_server.route('/accept_app/')
@db_session
def accept_app():
    user = session.get('mavapa_account')
    auth_url = session.get('auth_url')
    auth_url = urllib.unquote(auth_url)
    client_id = session.get('client_id')
    redirect_uri = session.get('redirect_uri')
    redirect_uri = urllib.unquote(redirect_uri)
    accepted = request.args.get('accepted')

    app = get_data('App', client_id=client_id, redirect_uri=redirect_uri)
    if accepted and user and auth_url:
        accepted = int(accepted)
        session.pop('auth_url')
        session.pop('client_id')
        session.pop('redirect_uri')
        if accepted:
            account = get_data('User', email=user)
            app = get_data('App', client_id=client_id, redirect_uri=redirect_uri)
            account.apps.add(app)
            commit()
            return redirect(auth_url)
        return redirect(url_for('index'))
    ctx = {'app_name': app.name, 'app_desc': app.desc, 'app_icon': app.icon}
    return render_template('accept_app.html', ctx=ctx)

@mavapa_server.route('/auth')
@db_session
def auth():
    """ Check if account is related to app """
    user = session.get('mavapa_account')
    if not user:
        login_url = url_for('login')
        session['next_url'] = request.url
        return redirect(login_url)
    account = get_data('User', email=user)
    response_type = request.args.get('response_type')
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    redirect_uri = urllib.unquote(redirect_uri)
    scopes = request.args.get('scopes')
    if scopes:
        scopes = scopes.split(',')
    app = get_data('App', client_id=client_id, redirect_uri=redirect_uri)
    if app:
        if app not in account.apps:
            session['auth_url'] = request.url
            session['client_id'] = client_id
            session['redirect_uri'] = redirect_uri
            return redirect(url_for('mavapa_server.accept_app'))
        url = app.redirect_uri
        code = make_rnd_str()
        url += '?code=' + code
        save_code(app, account, code)
        return redirect(url)
    data = {
        'response_type': response_type,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scopes': scopes,
    }
    return jsonify(data)

