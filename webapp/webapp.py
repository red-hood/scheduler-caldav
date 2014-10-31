#!/usr/bin/env python2

from flask import Flask
from flask import render_template, Response, request, url_for, make_response, abort

import caldav
import urlparse
import json
import requests as requests_native
import urllib

from scheduler import SchedulerCalendar, SchedulerEvent

def requests_raise(response, *args, **kwargs):
    response.raise_for_status()

app = Flask(__name__)
app.debug = True
requests = requests_native.Session()
requests.hooks={"response": requests_raise}

# TODO read from config file
cal_user = 'system'
permission_url = 'http://localhost:5001'
permission_templ = "/user/{}/permissions/calendar/{}"
auth_templ = "/user/auth"
url = 'http://system:system@localhost:5232/test/Calendar.ics/'
client = caldav.DAVClient(url)
sc_name = "sid"


def get_user(req):
    auth_url = urlparse.urljoin(permission_url, auth_templ)
    if sc_name in req.cookies:
        session_cookie = req.cookies[sc_name]
        cookies = {sc_name: session_cookie}
        response = requests.get(auth_url, cookies=cookies)
        return response.content


# TODO cal name in model
def check_permission(cal, user, want):
    # TODO implicit unsafety, like Jinja2
    cal_qt = urllib.quote_plus(cal)
    user_qt = urllib.quote_plus(user)
    permission_path = permission_templ.format(user_qt, cal_qt)
    req_url = urlparse.urljoin(permission_url, permission_path)
    resp = requests.get(req_url)
    try:
        return want in resp.content
    except:
        return False


def check_user_permission(cal, req, want):
    try:
        user = get_user(req)
        return check_permission(cal, user, want)
    except:
        return False

# TODO use different calendars


def get_system_cal(cal_name):
    # TODO custom context to hold client and calendar
    global cal_user
    return caldav.Calendar(client, '/' + cal_user + '/' + cal_name + '.ics/')


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
    # BEHOLD!
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
    app.run()
