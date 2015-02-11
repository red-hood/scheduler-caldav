#!/usr/bin/env python2

from flask import Flask
from flask import request, abort, make_response
import json

app = Flask(__name__)
app.debug = True

CREDS = 'creds'
API = '/api'

with open('./acl.json') as acl_file:
    acl = json.load(acl_file)


def api_route(route, methods=['GET']):
    return app.route(API + route, methods=methods)


@api_route('/user/<user>/permissions/calendars')
def user_permission(user):
    try:
        return json.dumps(acl['users'][user]['calendar'])
    except KeyError:
        abort(404)


@api_route('/user/<user>/permissions/calendars/<cal>')
def cal_permissions(user, cal):
    try:
        return acl['users'][user]['calendar'][cal]
    except KeyError:
        abort(404)


@api_route('/user/auth', methods=['POST', 'GET'])
def auth():
    method = request.method
    if method == 'POST':
        print(request.form)
        user = request.form['user']
        password = request.form['password']
        return auth_post(user, password)
    elif method == 'GET':
        sid = request.cookies.get('sid')
        return auth_cookie(sid)
    else:
        abort(503)


def auth_post(user, password):
    try:
        if (acl[CREDS][user] == password):
            return make_response('true', 200)
        else:
            abort(403)
    except KeyError:
        abort(404)


def auth_cookie(sid):
    if sid in acl[CREDS].keys():
        return make_response('true', 200)
    else:
        abort(403)


if __name__ == '__main__':
    app.run(port=5008)
