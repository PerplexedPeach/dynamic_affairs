import enum
import typing

debug = True


class EventsFirst(enum.IntEnum):
    MEETING_WITH_SPOUSE = 1


class EventsSex(enum.IntEnum):
    HANDJOB_TEASE = 1


class EventsCum(enum.IntEnum):
    HANDJOB_CUM_IN_HAND = 1


# alias for any event type
EventId = typing.Union[EventsFirst, EventsSex, EventsCum]

# common keywords (avoid and catch typos)
SCOPE = "scope"
MODIFIER = "modifier"
DESC = "desc"
TRIGGER = "trigger"
ANIMATION = "animation"
FIRST_VALID = "first_valid"
TRIGGERED_DESC = "triggered_desc"
LEFT_PORTRAIT = "left_portrait"
RIGHT_PORTRAIT = "right_portrait"
IMMEDIATE = "immediate"
OPTION = "option"
TARGET = "target"
OPINION = "opinion"
TITLE = "title"
THEME = "theme"
TYPE = "type"
NAME = "name"
VALUE = "value"
CUSTOM_TOOLTIP = "custom_tooltip"

CHARACTER_EVENT = "character_event"
CHARACTER = "character"

DOMINANT_OPINION = "dominant_opinion"
ROOT = "root"
AFFAIRS_PARTNER = "scope:affairs_partner"

ROOT_STAMINA = "scope:root_stamina"
PARNTER_STAMINA = "scope:partner_stamina"
DOM_SUCCESS = "scope:dom_success"

# effects
TRIGGER_EVENT = "trigger_event"
IF = "if"
LIMIT = "limit"
ELSE = "else"
HIDDEN_EFFECT = "hidden_effect"
REVERSE_ADD_OPINION = "reverse_add_opinion"
CALCULATE_DOM_SUCCESS_EFFECT = "calculate_dom_success_effect"
YES = "yes"
EXISTS = "exists"
NOT = "NOT"

LIDA_ONGOING_SEX_EFFECT = "lida_ongoing_sex_effect"
STAMINA_COST_1 = "STAMINA_COST_1"
STAMINA_COST_2 = "STAMINA_COST_2"

SAVE_SCOPE_VALUE_AS = "save_scope_value_as"
RANDOM = "random"
RANDOM_LIST = "random_list"

DEBUG_LOG_SCOPES = "debug_log_scopes"

SEX_TRANSITION = "sex_transition"
DOM_TRANSITION = "dom_transition"
SUB_TRANSITION = "sub_transition"
CUM_TRANSITION = "cum_transition"

dom_fail_offset = 10000


def event_type_namespace(id: EventId) -> str:
    if isinstance(id, EventsFirst):
        return "LIDAf"
    if isinstance(id, EventsSex):
        return "LIDAs"
    if isinstance(id, EventsCum):
        return "LIDAc"
    raise RuntimeError(f"Unrecognized event ID {id}")


def event_type_file(id: EventId) -> str:
    if isinstance(id, EventsFirst):
        return "events/LIDA_first_events.txt"
    if isinstance(id, EventsSex):
        return "events/LIDA_sex_events.txt"
    if isinstance(id, EventsCum):
        return "events/LIDA_cum_events.txt"
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

        namespace = event_type_namespace(self.id)
        id = int(self.id)
        self.fullname = f"{namespace}.{id}"

        self.options = options
        # to be computed in a backwards pass to see what options come into this event
        self.incoming_options = []

        self.custom_desc = custom_desc
        self.custom_immediate_effect = custom_immediate_effect

        self.root_female = root_female

        # temporary data when generating the string representation
        self._lines = []
        self._indent = 0

    def add_line(self, text: str):
        self._lines.append("\t" * self._indent + text)

    def add_debug_line(self, *args):
        if debug:
            self.add_line(*args)

    def __repr__(self):
        """Turn the event into a self string; will be called sequentially on the events to generate them"""
        self._lines = []
        with Block(self, self.fullname):
            self.add_line(f"# {self.title}")
            self.add_line(f"{TYPE} = {CHARACTER_EVENT}")
            self.add_line(f"{TITLE} = {self.fullname}.t")
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

            self.generate_options()

        return "\n".join(self._lines)

    def generate_desc(self):
        self.add_line(f"{DESC} = {self.fullname}.{DESC}")
        if self.custom_desc is not None:
            self.custom_desc(self)

    def generate_immediate_effect(self):
        if self.custom_immediate_effect is not None:
            self.custom_immediate_effect(self)

    def generate_options(self):
        pass

    def generate_hidden_opinion_change_effect(self, change):
        with Block(self, HIDDEN_EFFECT):
            with Block(self, REVERSE_ADD_OPINION):
                self.add_line(f"{TARGET} = {AFFAIRS_PARTNER}")
                self.add_line(f"{MODIFIER} = {DOMINANT_OPINION}")
                self.add_line(f"{OPINION} = {change}")


class OptionCategory(enum.IntEnum):
    SUB = 1
    DOM = 2
    CUM = 3
    OTHER = 4


class Option:
    """Directed edges in a scene graph, going from one event to another (or terminating)"""

    def __init__(self, next_id: EventId, category: OptionCategory, weight: int, transition_text: str,
                 failed_transition_text="",  # for dom options, have a chance to fail them
                 modifiers=(), triggers=()):
        self.next_id = next_id
        # TODO to be populated via backwards pass
        self.from_id = None
        self.id = None
        self.fullname = None
        self.next_event: typing.Optional[Event] = None
        self.from_event: typing.Optional[Event] = None

        self.category = category
        self.weight = weight
        self.transition_text = transition_text
        self.failed_transition_text = failed_transition_text

        self.modifiers = modifiers
        self.triggers = triggers

    def generate_modifiers_and_triggers(self, event: Event):
        for modifier in self.modifiers:
            event.add_line(f"{MODIFIER} = {{ {modifier} }}")
        for trigger in self.triggers:
            event.add_line(f"{TRIGGER} = {{ {trigger} }}")


class Sex(Event):
    def __init__(self, *args, stam_cost_1=0, stam_cost_2=0, **kwargs):
        self.stam_cost_1 = stam_cost_1
        self.stam_cost_2 = stam_cost_2
        super(Sex, self).__init__(*args, **kwargs)

    def generate_desc(self):
        # description of the transition from the previous event
        # TODO populate the reverse graph to see what options come into this event
        with Block(self, FIRST_VALID):
            for option in self.incoming_options:
                with Block(self, TRIGGERED_DESC):
                    with Block(self, TRIGGER):
                        self.add_line(f"{EXISTS} = {SCOPE}:{SEX_TRANSITION}")
                        self.add_line(f"{SCOPE}:{SEX_TRANSITION} = {option.id}")
                    self.add_line(f"{DESC} = {SEX_TRANSITION}_{option.id}")

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

    def generate_options_transition(self, options_list, option_transition_str):
        if len(options_list) == 0:
            return
        with Block(self, RANDOM_LIST):
            for option in options_list:
                with Block(self, f"{option.weight}"):
                    option.generate_modifiers_and_triggers(self)
                    with Block(self, f"{SAVE_SCOPE_VALUE_AS}"):
                        self.add_line(f"{NAME} = {option_transition_str}")
                        self.add_line(f"{VALUE} = {option.id}")

    def generate_immediate_effect(self):
        # calculate the success probability
        self.add_line(f"{CALCULATE_DOM_SUCCESS_EFFECT} = {YES}")
        with Block(self, LIDA_ONGOING_SEX_EFFECT):
            self.add_line(f"{STAMINA_COST_1} = {self.stam_cost_1}")
            self.add_line(f"{STAMINA_COST_2} = {self.stam_cost_2}")

        # separate into categories; within each category the outcome of which option gets selected is random
        categories_to_options = {c: [] for c in OptionCategory}
        for option in self.options:
            categories_to_options[option.category].append(option)

        # roll for both the dom and sub transitions
        for c, c_trans in [(OptionCategory.DOM, DOM_TRANSITION), (OptionCategory.SUB, SUB_TRANSITION)]:
            self.generate_options_transition(categories_to_options[c], c_trans)

        # additionally if there are cumming actions allow for these options
        options_list = categories_to_options[OptionCategory.CUM]
        if len(options_list) > 0:
            with Block(self, IF):
                with Block(self, LIMIT):
                    self.add_line(f"{PARNTER_STAMINA} <= 0")
                self.generate_options_transition(options_list, CUM_TRANSITION)

        super(Sex, self).generate_immediate_effect()

        self.add_debug_line(f"{DEBUG_LOG_SCOPES} = {YES}")

    def generate_options(self):
        categories_to_options = {c: [] for c in OptionCategory}
        for option in self.options:
            categories_to_options[option.category].append(option)

        # for c, c_trans in [(OptionCategory.DOM, DOM_TRANSITION), (OptionCategory.SUB, SUB_TRANSITION)]:
        #     options_list = categories_to_options[c]

        for option in self.options:
            with Block(self, OPTION):
                self.add_line(f"{NAME} = {option.fullname}")
                if option.tooltip is not None:
                    self.add_line(f"{CUSTOM_TOOLTIP} = {option.fullname}.tt")
                with Block(self, TRIGGER):
                    if option.category == OptionCategory.CUM:
                        self.add_line(f"{EXISTS} = {SCOPE}:{CUM_TRANSITION}")
                        self.add_line(f"{SCOPE}:{CUM_TRANSITION} = {option.id}")
                    elif option.category == OptionCategory.DOM:
                        self.add_line(f"{NOT} = {{ {EXISTS} = {SCOPE}:{CUM_TRANSITION} }}")
                        self.add_line(f"{SCOPE}:{DOM_TRANSITION} = {option.id}")
                    elif option.category == OptionCategory.SUB:
                        self.add_line(f"{NOT} = {{ {EXISTS} = {SCOPE}:{CUM_TRANSITION} }}")
                        self.add_line(f"{SCOPE}:{SUB_TRANSITION} = {option.id}")

                # for dom options, it could backfire and get you more dommed
                if option.category == OptionCategory.DOM:
                    self.generate_dom_option_effect(option, categories_to_options[OptionCategory.SUB])
                elif option.category == OptionCategory.SUB:
                    self.generate_sub_option_effect(option)
                elif option.cateory == OptionCategory.CUM:
                    self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")
                else:
                    raise RuntimeError(f"Unsupported option category {option.category}")

    def generate_sub_option_effect(self, option):
        self.generate_hidden_opinion_change_effect(-1)
        with Block(self, SAVE_SCOPE_VALUE_AS):
            self.add_line(f"{NAME} = {SEX_TRANSITION}")
            self.add_line(f"{VALUE} = {option.id}")
        self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")

    def generate_dom_option_effect(self, option, sub_options):
        with Block(self, IF):
            with Block(self, LIMIT):
                self.add_line(f"{DOM_SUCCESS} = {YES}")
            self.generate_hidden_opinion_change_effect(1)
            with Block(self, SAVE_SCOPE_VALUE_AS):
                self.add_line(f"{NAME} = {SEX_TRANSITION}")
                self.add_line(f"{VALUE} = {option.id}")
            self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")
        with Block(self, ELSE):
            self.generate_hidden_opinion_change_effect(-2)
            # register that we've failed to dom (use a large offset plus that ID)
            with Block(self, SAVE_SCOPE_VALUE_AS):
                self.add_line(f"{NAME} = {SEX_TRANSITION}")
                self.add_line(f"{VALUE} = {option.id + dom_fail_offset}")
            # for each possible sub transition check if we've sampled that
            for sub_option in sub_options:
                with Block(self, IF):
                    with Block(self, LIMIT):
                        self.add_line(f"{SCOPE}:{SUB_TRANSITION} = {sub_option.id}")
                    self.add_line(f"{TRIGGER_EVENT} = {sub_option.next_event.fullname}")


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

class EventMap:
    def __init__(self):
        self.events = {}

    def add(self, event: Event):
        self.events[event.id] = event

    def __getitem__(self, event_id: EventId):
        return self.events[event_id]


# TODO validate events (no disconnected events; have at least some in-edge or out-edge)

if __name__ == "__main__":
    e = Sex(EventsSex.HANDJOB_TEASE, "Handjob Tease", "handjob tease common description")
    print(e)
