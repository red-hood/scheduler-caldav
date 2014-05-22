from lxml.etree import Element, SubElement, CDATA,  tostring

time_format = '%Y-%m-%d %H:%M'


# TODO: expand RRULES
# create XML from dst/xslt
# make class from scheduler event with class methods
def schedulerEvent(id, text, start, end):
        root = Element('event', id=id)

        # SubElement does not allow to specify a CDATA element in the text
        # attribute during creation
        ctext = CDATA(text)
        elem_text = Element('text')
        elem_text.text = ctext
        root.append(elem_text)

        start_elem = SubElement(root, 'start_date')
        start_elem.text = start.strftime(time_format)
        end_elem = SubElement(root, 'end_date')
        end_elem.text = end.strftime(time_format)
        return root


def _getEventValue(calevent, key):
    val = getattr(calevent.instance.vevent, key).value
    if isinstance(val, CDATA):
        val = val.value
    return val


def _schedulerEventfromCalEv(calevent):
    ical_scheduler_map = {
        'id': 'uid',
        'text': 'summary',
        'start': 'dtstart',
        'end': 'dtend',
    }

    scheduler_vals = {key: _getEventValue(calevent, val) for key, val
                      in ical_scheduler_map.iteritems()}

    return schedulerEvent(**scheduler_vals)


def schedulerEventsfromCaleEvs(calevents):
    for ev in calevents:
        ev.load()

    # filter for other event types, e.g. VTODO, we can not display them in the
    # calendar
    return [_schedulerEventfromCalEv(ev) for ev in calevents if
            hasattr(ev.instance, 'vevent')]


def schedulerContainerData(scheduler_events, pretty_print=True):
    root = Element('data')
    for ev in scheduler_events:
        root.append(ev)

    return tostring(root, pretty_print=pretty_print)


# just for test, not belongs here
def schedulerDataFromCal(cal):
    cevs = cal.events()
    sevs = schedulerEventsfromCaleEvs(cevs)
    return schedulerContainerData(sevs)
