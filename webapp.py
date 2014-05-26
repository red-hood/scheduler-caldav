#!/usr/bin/env python2

from flask import Flask
import caldav
import scheduler_adapter


app = Flask(__name__)


@app.route('/events')
def getAllEvents():
    url = 'http://test:test@localhost:5232/test/Calendar.ics/'
    client = caldav.DAVClient(url)
    cal = caldav.Calendar(client, '/test/calendar.ics/')
    return scheduler_adapter.schedulerDataFromCal(cal)

if __name__ == '__main__':
    app.run()
