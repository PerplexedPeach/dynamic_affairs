import enum
import typing


class EventsFirst(enum.IntEnum):
    MEETING_WITH_SPOUSE = 1


class EventsSex(enum.IntEnum):
    HANDJOB_TEASE = 1


class EventsCum(enum.IntEnum):
    HANDJOB_CUM_IN_HAND = 1


# alias for any event type
EventId = typing.Union[EventsFirst, EventsSex, EventsCum]


def event_type_namespace(id: EventId) -> str:
    if isinstance(id, EventsFirst):
        return "LIDAf"
    if isinstance(id, EventsSex):
        return "LIDAs"
    if isinstance(id, EventsCum):
        return "LIDAc"
    raise RuntimeError(f"Unrecognized event ID {id}")


class Event:
    def __init__(self, id: EventId, title="Placeholder title", desc="placeholder event desc"):
        self.id = id
        self.title = title
        self.desc = desc

        # temporary data when generating the string representation
        self._lines = []
        self._indent = 0

    def add_line(self, text: str):
        self._lines.append("\t" * self._indent + text)

    def __repr__(self):
        """Turn the event into a self string; will be called sequentially on the events to generate them"""
        self._lines = []
        namespace = event_type_namespace(self.id)
        id = int(self.id)
        fullname = f"{namespace}.{id}"
        with Block(self, fullname):
            self.add_line("type = character_event")
            self.add_line(f"title = {fullname}.t")
        return "\n".join(self._lines)


class Block:
    """Context manager for nesting blocks of = {} with proper indentation"""
    def __init__(self, event: Event, left_hand_side: str):
        self.event = event
        self.event.add_line(f"{left_hand_side} = {{")

    def __enter__(self):
        self.event._indent += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.event._indent -= 1
        self.event.add_line("}")


# TODO define directed graph of events

class EventGroup:
    def __init__(self, path, event_class: typing.Type[EventId]):
        self.path = path
        self.event_class = event_class
        self.namespace = event_type_namespace(event_class(1))
        self.events = []

    def add(self, event: Event):
        self.events.append(event)


first_events = EventGroup("events/LIDA_first_events.txt", EventsFirst)
sex_events = EventGroup("events/LIDA_sex_events.txt", EventsSex)
cum_events = EventGroup("events/LIDA_cum_events.txt", EventsCum)

# TODO validate events (no disconnected events; have at least some in-edge or out-edge)

if __name__ == "__main__":
    e = Event(EventsSex.HANDJOB_TEASE, "Handjob Tease", "handjob tease common description")
    print(e)
