#!/usr/bin/env python2

from flask import Flask
from flask import render_template, Response, request

import caldav
from scheduler import SchedulerCalendar, SchedulerEvent


app = Flask(__name__)
app.debug = True

# TODO read from config file
cal_user = 'system'

def get_system_cal(cal_name):
    # TODO custom context to hold client and calendar
    global cal_user
    return caldav.Calendar(client, '/' + cal_user + '/' + cal_name + '.ics/')


# TODO use different calendars
url = 'http://system:system@localhost:5232/test/Calendar.ics/'
client = caldav.DAVClient(url)


@app.route('/calendar/<cal>')
def calendar(cal):
    return render_template('index.html', cal=cal)


# fake auth resource to test
@app.route('/auth')
def auth(request):
    cookie = request.cookies['sid']
    print cookie


# read only resource to retrieve all events
@app.route('/events/<cal>')
def events(cal):
    # BEHOLD!
    dav_cal = get_system_cal(cal)
    sched_cal = SchedulerCalendar.fromCalendar(dav_cal)
    return sched_cal.toXMLString()


# modify single events
# TODO check if id/ref belongs to calendars, otherwise security hole!
@app.route('/event/<cal>', methods=['POST'])
def event(cal):
    dav_cal = get_system_cal(cal)
    start = request.form['start_date']
    end = request.form['end_date']
    text = request.form['text']
    id = request.form['id']
    tid = id

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
