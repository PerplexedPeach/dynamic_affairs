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

# common keywords (avoid and catch typos)
DESC = "desc"
TRIGGER = "trigger"
ANIMATION = "animation"
FIRST_VALID = "first_valid"
TRIGGERED_DESC = "triggered_desc"
LEFT_PORTRAIT = "left_portrait"
RIGHT_PORTRAIT = "right_portrait"
IMMEDIATE = "immediate"
OPTION = "option"
IF = "if"
ELSE = "else"
HIDDEN_EFFECT = "hidden_effect"
TITLE = "title"
THEME = "theme"
TYPE = "type"
CHARACTER_EVENT = "character_event"
CHARACTER = "character"

ROOT = "root"
AFFAIRS_PARTNER = "scope:affairs_partner"

ROOT_STAMINA = "scope:root_stamina"
PARNTER_STAMINA = "scope:partner_stamina"

CALCULATE_DOM_SUCCESS_EFFECT = "calculate_dom_success_effect"
YES = "yes"

LIDA_ONGOING_SEX_EFFECT = "lida_ongoing_sex_effect"
STAMINA_COST_1 = "STAMINA_COST_1"
STAMINA_COST_2 = "STAMINA_COST_2"

DEBUG_LOG_SCOPES = "debug_log_scopes"


def event_type_namespace(id: EventId) -> str:
    if isinstance(id, EventsFirst):
        return "LIDAf"
    if isinstance(id, EventsSex):
        return "LIDAs"
    if isinstance(id, EventsCum):
        return "LIDAc"
    raise RuntimeError(f"Unrecognized event ID {id}")


class Event:
    """Vertices in a scene graph, each corresponding to a specific scene"""

    def __init__(self, id: EventId, title="Placeholder title", desc="placeholder event desc", theme="seduction",
                 animation_left="flirtation", animation_right="flirtation_left", options=(),
                 root_female=True,
                 # custom generation functions, these take the event as teh first argument and call add_line
                 custom_desc: typing.Optional[typing.Callable] = None,
                 custom_immediate_effect: typing.Optional[typing.Callable] = None):
        self.id = id
        self.title = title
        self.desc = desc
        self.theme = theme
        self.anim_l = animation_left
        self.anim_r = animation_right
        self.options = options
        self.custom_desc = custom_desc
        self.custom_immediate_effect = custom_immediate_effect

        self.debug = True
        self.root_female = root_female

        # temporary data when generating the string representation
        self._lines = []
        self._indent = 0

    def add_line(self, text: str):
        self._lines.append("\t" * self._indent + text)

    def add_debug_line(self, *args):
        if self.debug:
            self.add_line(*args)

    def fullname(self):
        namespace = event_type_namespace(self.id)
        id = int(self.id)
        return f"{namespace}.{id}"

    def __repr__(self):
        """Turn the event into a self string; will be called sequentially on the events to generate them"""
        self._lines = []
        fullname = self.fullname()
        with Block(self, fullname):
            self.add_line(f"# {self.title}")
            self.add_line(f"{TYPE} = {CHARACTER_EVENT}")
            self.add_line(f"{TITLE} = {fullname}.t")
            self.add_line(f"{THEME} = {self.theme}")
            with Block(self, LEFT_PORTRAIT):
                self.add_line(f"{CHARACTER} = {ROOT}")
                self.add_line(f"{ANIMATION} = {self.anim_l}")
            with Block(self, RIGHT_PORTRAIT):
                self.add_line(f"{CHARACTER} = {AFFAIRS_PARTNER}")
                self.add_line(f"{CHARACTER} = {self.anim_r}")

            with Block(self, DESC):
                self.generate_desc()
            with Block(self, IMMEDIATE):
                self.generate_immediate_effect()

            for option in self.options:
                # TODO who's responsibility is it to generate the option
                with Block(self, OPTION):
                    self.generate_option(option)

        return "\n".join(self._lines)

    def generate_desc(self):
        self.add_line(f"{DESC} = {self.fullname()}.{DESC}")
        if self.custom_desc is not None:
            self.custom_desc(self)

    def generate_immediate_effect(self):
        if self.custom_immediate_effect is not None:
            self.custom_immediate_effect(self)

    def generate_option(self, option):
        pass


class Option:
    """Directed edges in a scene graph, going from one event to another (or terminating)"""

    def __init__(self, next_id: EventId):
        self.next_id = next_id


class Sex(Event):
    def __init__(self, *args, stam_cost_1=0, stam_cost_2=0, **kwargs):
        self.stam_cost_1 = stam_cost_1
        self.stam_cost_2 = stam_cost_2
        super(Sex, self).__init__(*args, **kwargs)

    def generate_desc(self):
        # description of each partners' stamina
        stamina_thresholds = {2: "very_low", 3: "low", 4: "med"}
        first_prefix = "f"
        second_prefix = "m"
        if not self.root_female:
            first_prefix = "rm"
            second_prefix = "rf"

        for prefix, value_to_check in [(first_prefix, ROOT_STAMINA), (second_prefix, PARNTER_STAMINA)]:
            with Block(self, FIRST_VALID):
                for threshold, suffix in stamina_thresholds.items():
                    with Block(self, TRIGGERED_DESC):
                        with Block(self, TRIGGER):
                            self.add_line(f"{value_to_check} < {threshold}")
                        self.add_line(f"{DESC} = {prefix}_{suffix}_stam")
                    # backup option for high stamina
                    self.add_line(f"{DESC} = {prefix}_high_stam")

    def generate_immediate_effect(self):
        # calculate the success probability
        self.add_line(f"{CALCULATE_DOM_SUCCESS_EFFECT} = {YES}")
        with Block(self, LIDA_ONGOING_SEX_EFFECT):
            self.add_line(f"{STAMINA_COST_1} = {self.stam_cost_1}")
            self.add_line(f"{STAMINA_COST_2} = {self.stam_cost_2}")
        self.add_line(f"{DEBUG_LOG_SCOPES} = {YES}")


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
    e = Sex(EventsSex.HANDJOB_TEASE, "Handjob Tease", "handjob tease common description")
    print(e)
