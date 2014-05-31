#!/usr/bin/env python2

from flask import Flask
from flask import render_template, Response, request

import caldav
from scheduler import SchedulerCalendar, SchedulerEvent


app = Flask(__name__)
app.debug = True


# TODO use different calendars
url = 'http://test:test@localhost:5232/test/Calendar.ics/'
client = caldav.DAVClient(url)
cal = caldav.Calendar(client, '/test/calendar.ics/')


@app.route('/')
def index():
    return render_template('index.html')


# read only resource to retrieve all events
@app.route('/events')
def getAllEvents():
    sched_cal = SchedulerCalendar.fromCalendar(cal)
    return sched_cal.toXMLString()


# modify single events
@app.route('/event', methods=['POST'])
def createOrUpdate():
    start = request.form['start_date']
    end = request.form['end_date']
    text = request.form['text']
    id = request.form['id']

    mode = request.form['!nativeeditor_status']
    tid = id

    # TODO views for update and delete, with different status codes
    if mode == 'updated':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.update(cal)
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=200,
            mimetype='application/xml')
    elif mode == 'inserted':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.create(cal)
        # use original id only in reponse
        tid = ev.id
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=201,
            mimetype='application/xml')
    elif mode == 'deleted':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.delete(cal)
        return Response(
            SchedulerEvent.XmlResponse(mode, id, tid),
            status=200,
            mimetype='application/xml')


if __name__ == '__main__':
    app.run()
