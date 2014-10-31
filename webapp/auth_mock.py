#!/usr/bin/env python2

from flask import Flask
from flask import render_template, Response, request, url_for, abort
import json

app = Flask(__name__)
app.debug = True

with open('./acl.json') as acl_file:
    acl = json.load(acl_file)


@app.route('/user/<user>/permissions/calendars')
def user_permission(user):
    try:
        return json.dumps(acl['users'][user]['calendar'])
    except KeyError:
        abort(404)


@app.route("/user/<user>/permissions/calendars/<cal>")
def cal_permissions(user, cal):
    try:
        return acl['users'][user]['calendar'][cal]
    except KeyError:
        abort(404)


@app.route('/user/auth')
def auth():
    return request.cookies['sid']

if __name__ == '__main__':
    app.run(port=5001)
