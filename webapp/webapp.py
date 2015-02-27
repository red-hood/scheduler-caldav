#!/usr/bin/env python2

from flask import Flask
from flask import render_template, Response, request, url_for, make_response, abort

import caldav
import requests as requests_native
import urllib
import os

try:
    import ConfigParser as configparser
except:
    import configparser

from scheduler import SchedulerCalendar, SchedulerEvent


def requests_raise(response, *args, **kwargs):
    response.raise_for_status()

app = Flask(__name__)
app.debug = True
# TODO read from config file
cal_user = 'ws2'
cal_user_pw = '2342'
auth_url_templ = "http://localhost:5008/api/auth"
permission_url_templ = "http://localhost:5008/api/user/{user}/permissions/calendars/{calendar}"
# TODO add authentication with urllib/caldav client lib
cal_client_url_templ = "http://{cal_user}:{cal_user_pw}@localhost:5232/caldav/{cal_user}"
cal_path_templ = "/caldav/{cal_user}/{calendar}"
sc_name = "sid"


# TODO can we do a client connection w/o a calendar?
def get_client():
    client_url = cal_client_url_templ.format(
        cal_user=cal_user,
        cal_user_pw=cal_user_pw,
    )
    return caldav.DAVClient(client_url)


def get_config(conf_file='./config'):
    file_name = os.environ['CALDAV_MW_CONFIG'] or conf_file
    with open(file_name) as f:
        config = configparser.SafeConfigParser(f)
    return config

def get_user(req):
    session_cookie = req.cookies[sc_name]
    auth_url = auth_url_templ.format(session_cookie)
    cookies = {sc_name: session_cookie}
    response = requests.get(auth_url, cookies=cookies)
    app.logger.debug('Got user {} for session cookie {}.'.format(
        session_cookie, response))
    return response.content


# TODO cal name in model
def check_permission(cal, user, want):
    # TODO implicit unsafety, like Jinja2
    cal_qt = urllib.quote_plus(cal)
    user_qt = urllib.quote_plus(user)
    permission_url = permission_url_templ.format(user=user_qt, calendar=cal_qt)
    resp = requests.get(permission_url)
    app.logger.debug('Got permission {} for user {} wanting {}.'.format(
        resp, user, want))
    return want in resp.content


def check_user_permission(cal, req, want):
    try:
        user = get_user(req)
        return check_permission(cal, user, want)
    except:
        return False


def get_cal_path(cal_user, cal_name):
    return cal_path_templ.format(cal_user=cal_user, calendar=cal_name)


def get_system_cal(cal_name):
    # TODO custom context to hold client and calendar
    global cal_user
    cal_path = get_cal_path(cal_user, cal_name)
    return caldav.Calendar(client, cal_path)


@app.route('/calendar/<cal>')
def calendar(cal):
    resp = make_response(render_template('index.html', cal=cal))
    resp.set_cookie('sid', 'user1')
    return resp


"""
cals: Comma seperated list of calendars to display
"""
@app.route('/calendars/<cals>')
def calendars(cals):
        cal_list = cals.split(',')
        cal_urls = [url_for('events', cal=cal) for cal in cal_list]
        return render_template('multisource.html', cal_urls=cal_urls)


@app.template_filter('quote')
def quote(text, quote_mark='"'):
    return quote_mark + text + quote_mark


@app.route('/events/<cal>')
def events(cal):
    dav_cal = get_system_cal(cal)
    if check_user_permission(cal, request, 'r'):
        # TODO have SchedulerCalendar handle name resolution
        sched_cal = SchedulerCalendar.fromCalendar(dav_cal)
        return sched_cal.toXMLString()
    else:
        abort(403)


# modify single events
@app.route('/event/<cal>', methods=['POST'])
def event(cal):
    # get calendar from id
    #
    start = request.form['start_date']
    end = request.form['end_date']
    text = request.form['text']
    id = request.form['id']
    tid = id

# TODO check if id/ref belongs to calendars, otherwise security hole!
    #url_cal = url.path.split('/')[1].rstrip('.ics')
    #url = urlparse.urlparse(id)
    dav_cal = get_system_cal(cal)

    mode = request.form['!nativeeditor_status']

    # TODO views for update and delete, with different status codes
    if mode == 'updated':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.update(dav_cal)
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=200,
            mimetype='application/xml')
    elif mode == 'inserted':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.create(dav_cal)
        # use original id only in reponse
        tid = ev.id
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=201,
            mimetype='application/xml')
    elif mode == 'deleted':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.delete(dav_cal)
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=200,
            mimetype='application/xml')


if __name__ == '__main__':
    requests = requests_native.Session()
    requests.hooks = {"response": requests_raise}
    config = get_config()
    client = get_client()
    app.run()
