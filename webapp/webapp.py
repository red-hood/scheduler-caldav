#!/usr/bin/env python2

from flask import Flask
from flask import render_template
from flask import request

import caldav
from scheduler import SchedulerCalendar


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
    attr_list = ['id', 'start_date', 'end_date', 'text']
    for attr in attr_list:
        print(request.form[attr])
    return ""


if __name__ == '__main__':
    app.run()
