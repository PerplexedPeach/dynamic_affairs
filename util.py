import re

from defines import EventId, EventsFirst, FIRST_NAMESPACE, EventsSex, SEX_NAMESPACE, EventsCum, CUM_NAMESPACE


def clean_str(string):
    return re.sub(' +', ' ', string.strip().replace('\n', '')).replace('\\n\\n ', '\\n\\n')


def event_type_namespace(eid: EventId) -> str:
    if isinstance(eid, EventsFirst):
        return FIRST_NAMESPACE
    if isinstance(eid, EventsSex):
        return SEX_NAMESPACE
    if isinstance(eid, EventsCum):
        return CUM_NAMESPACE
    raise RuntimeError(f"Unrecognized event ID {eid}")
