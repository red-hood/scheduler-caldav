from lxml.etree import Element, SubElement, CDATA,  tostring
import sys

time_format = '%Y-%m-%d %H:%M'


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


class SchedulerEvent(object):
    def __init__(self, id, start, end, text=""):
        if text is None:
            text = ""

        self.id = id
        self.start = start
        self.end = end
        self.text = text

    def toXml(self, pretty_print=True):
        # TODO: output with objectify
        root = Element('event', id=self.id)

        # SubElement does not allow to specify a CDATA element in the text
        # attribute during creation
        ctext = CDATA(self.text)
        elem_text = Element('text')
        elem_text.text = ctext
        root.append(elem_text)

        start_elem = SubElement(root, 'start_date')
        start_elem.text = self.start.strftime(time_format)
        end_elem = SubElement(root, 'end_date')
        end_elem.text = self.end.strftime(time_format)
        return root

    @classmethod
    def fromCalEvent(cls, cal_event):
        ical_scheduler_map = {
            'id': 'uid',
            'text': 'summary',
            'start': 'dtstart',
            'end': 'dtend',
        }

        scheduler_vals = {key: _getEventValue(cal_event, val) for key, val
                          in ical_scheduler_map.iteritems()}
        return cls(**scheduler_vals)


# container for the ScheduverEvents
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

    # TODO: in container for caldav calendar
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
