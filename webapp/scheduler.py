import sys
import datetime
import uuid
from lxml.etree import Element, SubElement, CDATA,  tostring
from lxml import objectify
from vobject import icalendar, iCalendar


time_format = '%Y-%m-%d %H:%M'

ical_scheduler_map = {
    'text': 'summary',
    'start': 'dtstart',
    'end': 'dtend',
}


# helper  method
# TODO add to event wrapper class
def _getEventValue(calevent, key):
    try:
        val = getattr(calevent.instance.vevent, key).value
    except AttributeError as e:
        print(e)
        return None
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    if isinstance(val, CDATA):
        val = val.value

    return val


# TODO: implement proxy property to convert between local and utc
# objects
class SchedulerEvent(object):

    def __init__(self, id, start, end, text=""):
        if text is None:
            text = ""

        self.id = id
        self.start = start
        self.end = end
        self.text = text

    # TODO to Json/Dict
    def toXml(self, pretty_print=True, offset="-120"):
        # TODO: output with objectify
        root = Element('event', id=self.id)

        # SubElement does not allow to specify a CDATA element in the text
        # attribute during creation
        ctext = CDATA(self.text)
        elem_text = Element('text')
        elem_text.text = ctext
        root.append(elem_text)

        start_elem = SubElement(root, 'start_date')
        start_elem.text = \
            self._localTime(self.start, offset).strftime(time_format)
        end_elem = SubElement(root, 'end_date')
        end_elem.text = self._localTime(self.end, offset).strftime(time_format)
        return root

    @staticmethod
    def _localTime(dt, offset):
        offset = int(offset)
        delta = datetime.timedelta(minutes=-offset)
        return dt + delta

    @staticmethod
    def _utcTime(str_time, offset):
        utc = icalendar.utc
        offset = int(offset)
        delta = datetime.timedelta(minutes=offset)
        naive_date = datetime.datetime.strptime(str_time, time_format)
        utc_date = naive_date + delta
        utc_date = utc_date.replace(tzinfo=utc)
        return utc_date

    @classmethod
    def fromCalEvent(cls, cal_event):
        scheduler_vals = {key: _getEventValue(cal_event, val) for key, val
                          in ical_scheduler_map.iteritems()}
        id = cal_event.url.url_parsed.path
        scheduler_vals.update({'id': id})
        return cls(**scheduler_vals)

    # TODO how to get the timeshift in post parameters?
    @classmethod
    def fromRequest(cls, id, str_start, str_end, text, offset='-120'):
        id = unicode(id)
        text = unicode(text)
        offset = int(offset)
        start = cls._utcTime(str_start, offset)
        end = cls._utcTime(str_end, offset)
        return cls(id, start, end, text)

    def create(self, cal):
        cal_entry = iCalendar()
        ev = cal_entry.add('vevent')
        ev.add('summary').value = self.text
        ev.add('dtstart').value = self.start
        ev.add('dtend').value = self.end
        uid = unicode(uuid.uuid4())
        ev.add('uid').value = uid

        cal_event = cal.add_event(cal_entry.serialize())

        # TODO use url here as scheduler id, not uid
        # should be decoupled
        # update own id from caldav uid
        self.id = cal_event.url.url_parsed.path

    # TODO set modified date and increase sequence
    def update(self, cal):
        # TODO SEC attacker migh pass URL of other calendar
        event = cal.event_by_url(self.id)
        event.load()
        # TODO how to create a new dtstart entry?

        # UGLY! maybe create a new one, then merge? only cause of tzinfo is
        # saved in params
        # use vobject.newFromBehavior() to generate a new dtstart/dtend?
        # dtstart = vobject.newFromBehavior('dtstart')
        # dtstart.isNative=True
        # dtstart.value = datetimeObj
        # use dict.update to merge
        event.instance.vevent.dtstart.params = {}
        event.instance.vevent.dtend.params = {}
        event.instance.vevent.dtstart.value = self.start
        event.instance.vevent.dtend.value = self.end
        event.instance.vevent.summary.value = self.text
        event.save()

    def delete(self, cal):
        event = cal.event_by_url(self.id)
        event.delete()

    # TODO in view
    @staticmethod
    def XmlResponse(mode, id, tid):
        E = objectify.ElementMaker(annotate=False, namespace=None, nsmap=None)
        root = E.data(
            E.action(type=mode, sid=id, tid=tid)
        )
        return tostring(root)


# container for the ScheduverEvents
# TODO handle timeshift parameter
class SchedulerCalendar(list):

    def __init__(self, scheduler_events):
        super(SchedulerCalendar, self).__init__(scheduler_events)

    @classmethod
    def fromCalEvents(cls, cal_events, load=True):
        if load is True:
            cls._loadEvents(cal_events)
        events = [SchedulerEvent.fromCalEvent(ev) for ev in cal_events if
                  hasattr(ev.instance, 'vevent')]
        return cls(events)

    @classmethod
    def fromCalendar(self, caldav_calendar):
        cal_events = caldav_calendar.events()
        return self.fromCalEvents(cal_events)

    @staticmethod
    def _loadEvents(events):
        for ev in events:
            ev.load()

    def toXML(self):
        root = Element('data')
        for ev in self:
            root.append(ev.toXml())
        return root

    def toXMLString(self):
        return tostring(self.toXML(), pretty_print=True)
