#!/usr/bin/env python2

from flask import Flask
from flask import render_template
from flask import request

import caldav
from scheduler import SchedulerCalendar, SchedulerEvent


app = Flask(__name__)
app.debug = True


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
    attr_list = ['id', 'start_date', 'end_date', 'text', '!nativeeditor_status']
    for attr in attr_list:
        print(request.form[attr])

    mode = request.form['!nativeeditor_status']

    start = request.form['start_date']
    end = request.form['end_date']
    text = request.form['text']
    id = request.form['id']

    if mode == 'updated':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.update(cal)
        return ""
    elif mode == 'inserted':
        ev = SchedulerEvent.fromRequest(id, start, end, text)
        ev.save(cal)

    return ""


if __name__ == '__main__':
    app.run()
