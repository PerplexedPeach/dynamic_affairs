import enum
import typing
import argparse

UTF8_BOM = u'\ufeff'
debug = True


class EventsFirst(enum.IntEnum):
    MEETING_WITH_SPOUSE = 1


class EventsSex(enum.IntEnum):
    HANDJOB_TEASE = 1
    ASS_TEASE = 2
    HANDJOB = 3
    BLOWJOB_DOM = 4


class EventsCum(enum.IntEnum):
    HANDJOB_CUM_IN_HAND = 1
    BLOWJOB_CUM_IN_MOUTH_DOM = 2
    BLOWJOB_CUM_ON_FACE = 3
    BLOWJOB_RUINED_ORGASM = 4
    ASS_TEASE_CUM_ON_ASS = 5


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
NO = "no"
EXISTS = "exists"
NOT = "NOT"

LIDA_ONGOING_SEX_EFFECT = "lida_ongoing_sex_effect"
STAMINA_COST_1 = "STAMINA_COST_1"
STAMINA_COST_2 = "STAMINA_COST_2"
CHANGE_SUBDOM_EFFECT = "change_subdom_effect"
CHANGE = "CHANGE"
CARN_HAD_SEX_WITH_EFFECT = "carn_had_sex_with_effect"
CHARACTER_1 = "CHARACTER_1"
CHARACTER_2 = "CHARACTER_2"
C1_PREGNANCY_CHANCE = "C1_PREGNANCY_CHANCE"
C2_PREGNANCY_CHANCE = "C2_PREGNANCY_CHANCE"
STRESS_EFFECTS = "STRESS_EFFECTS"
DRAMA = "DRAMA"

SAVE_SCOPE_VALUE_AS = "save_scope_value_as"
RANDOM = "random"
RANDOM_LIST = "random_list"

DEBUG_LOG_SCOPES = "debug_log_scopes"

SEX_TRANSITION = "sex_transition"
DOM_TRANSITION = "dom_transition"
SUB_TRANSITION = "sub_transition"
CUM_TRANSITION = "cum_transition"

NAMESPACE = "namespace"
OPTION_NAMESPACE = "LIDAoption"
FIRST_NAMESPACE = "LIDAf"
SEX_NAMESPACE = "LIDAs"
CUM_NAMESPACE = "LIDAc"

L_ENGLISH = "l_english:"
EVENTS_FILE_HEADER = "# GENERATED FILE - DO NOT MODIFY DIRECTLY"

# localization constants
THEM = "[affairs_partner.GetFirstName]"

dom_fail_offset = 10000


def yes_no(boolean: bool):
    return YES if boolean else NO


def event_type_namespace(eid: EventId) -> str:
    if isinstance(eid, EventsFirst):
        return FIRST_NAMESPACE
    if isinstance(eid, EventsSex):
        return SEX_NAMESPACE
    if isinstance(eid, EventsCum):
        return CUM_NAMESPACE
    raise RuntimeError(f"Unrecognized event ID {eid}")


class Event:
    """Vertices in a scene graph, each corresponding to a specific scene"""

    def __init__(self, eid: EventId, title, desc="placeholder event desc", theme="seduction",
                 animation_left="flirtation", animation_right="flirtation_left", options=(),
                 root_female=True,
                 # custom generation functions, these take the event as teh first argument and call add_line
                 custom_desc: typing.Optional[typing.Callable] = None,
                 custom_immediate_effect: typing.Optional[typing.Callable] = None):
        self.id = eid
        self.title = title
        self.desc = desc
        self.theme = theme
        self.anim_l = animation_left
        self.anim_r = animation_right

        namespace = event_type_namespace(self.id)
        eid = int(self.id)
        self.fullname = f"{namespace}.{eid}"

        self.options: typing.Sequence[Option] = options
        # to be computed in a backwards pass to see what options come into this event
        self.incoming_options = []

        self.custom_desc = custom_desc
        self.custom_localization = None
        self.custom_immediate_effect = custom_immediate_effect

        self.root_female = root_female

        # temporary data when generating the string representation
        self._lines = []
        self._indent = 0

    def add_line(self, text: str):
        self._lines.append("\t" * self._indent + text)

    def add_comment(self, text: str):
        self.add_line("# " + text)

    def add_debug_line(self, *args):
        if debug:
            self.add_line(*args)

    def __repr__(self):
        """Turn the event into a self string; will be called sequentially on the events to generate them"""
        self._lines = []
        with Block(self, self.fullname):
            self.add_comment(self.title)
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
            # calling the custom desc will modify the event string text in place, and return a localization string
            self.custom_localization = self.custom_desc(self)

    def generate_immediate_effect(self):
        if self.custom_immediate_effect is not None:
            self.custom_immediate_effect(self)

    def generate_options(self):
        pass

    def generate_hidden_opinion_change_effect(self, change):
        with Block(self, CHANGE_SUBDOM_EFFECT):
            self.add_line(f"{CHANGE} = {change}")

    def generate_localization(self):
        lines = [f"{self.fullname}.t: \"{self.title}\"",
                 f"{self.fullname}.{DESC}: \"{self.desc}\""]
        if self.custom_localization is not None:
            lines.append(self.custom_localization)
        return "\n".join(lines)

    def generate_incoming_options_desc(self):
        # description of the transition from the previous event
        # populate the reverse graph to see what options come into this event
        with Block(self, FIRST_VALID):
            for option in self.incoming_options:
                with Block(self, TRIGGERED_DESC):
                    with Block(self, TRIGGER):
                        self.add_line(f"{EXISTS} = {SCOPE}:{SEX_TRANSITION}")
                        self.add_line(f"{SCOPE}:{SEX_TRANSITION} = {option.id}")
                    self.add_line(f"{DESC} = {SEX_TRANSITION}_{option.id}")


class OptionCategory(enum.IntEnum):
    SUB = 1
    DOM = 2
    CUM = 3
    OTHER = 4


class Option:
    """Directed edges in a scene graph, going from one event to another (or terminating)"""

    def __init__(self, next_id: typing.Optional[EventId], category: OptionCategory, transition_text: str,
                 # for dom options, have a chance to fail them
                 failed_transition_text="", weight: int = 10, tooltip=None,
                 subdom_dom_success=1, subdom_dom_fail=-2, subdom_sub=-1,
                 modifiers=(), triggers=()):
        self.next_id = next_id
        # to be populated via backwards pass
        self.from_id = None
        self.id = None
        self.fullname = None
        self.next_event: typing.Optional[Event] = None
        self.from_event: typing.Optional[Event] = None

        self.category = category
        self.weight = weight
        self.transition_text = transition_text
        self.failed_transition_text = failed_transition_text
        self.tooltip = tooltip

        self.subdom_dom_success = subdom_dom_success
        self.subdom_dom_fail = subdom_dom_fail
        self.subdom_sub = subdom_sub

        self.modifiers = modifiers
        self.triggers = triggers

    def generate_modifiers_and_triggers(self, event: Event):
        for modifier in self.modifiers:
            event.add_line(f"{MODIFIER} = {{ {modifier} }}")
        for trigger in self.triggers:
            event.add_line(f"{TRIGGER} = {{ {trigger} }}")

    def generate_localization(self):
        lines = [f"{self.fullname}: \"{self.transition_text}\"",
                 f"{OPTION_NAMESPACE}.{self.id + dom_fail_offset}: \"{self.failed_transition_text}\""]
        if self.tooltip is not None:
            lines.append(f"{self.fullname}.tt: \"{self.tooltip}\"")

        return "\n".join(lines)


class Cum(Event):
    def __init__(self, *args, terminal_option: Option, preg_chance_1: float = 0, preg_chance_2: float = 0,
                 subdom_change=0, stress_effects=True, drama=True, **kwargs):
        self.subdom_change = subdom_change
        self.preg_chance_1 = preg_chance_1
        self.preg_chance_2 = preg_chance_2
        self.stress_effects = stress_effects
        self.drama = drama
        super(Cum, self).__init__(*args, options=(terminal_option,), **kwargs)
        assert isinstance(self.id, EventsCum)

    def generate_desc(self):
        self.generate_incoming_options_desc()
        super(Cum, self).generate_desc()

    def generate_immediate_effect(self):
        # register that we have had sex to compute consequences
        # TODO see if this needs to be hidden or not, and also if we need to put this under option?
        with Block(self, HIDDEN_EFFECT):
            if self.subdom_change is not 0:
                self.generate_hidden_opinion_change_effect(self.subdom_change)
            with Block(self, CARN_HAD_SEX_WITH_EFFECT):
                self.add_line(f"{CHARACTER_1} = {ROOT}")
                self.add_line(f"{CHARACTER_2} = {AFFAIRS_PARTNER}")
                self.add_line(f"{C1_PREGNANCY_CHANCE} = {self.preg_chance_1}")
                self.add_line(f"{C2_PREGNANCY_CHANCE} = {self.preg_chance_2}")
                self.add_line(f"{STRESS_EFFECTS} = {yes_no(self.stress_effects)}")
                self.add_line(f"{DRAMA} = {yes_no(self.drama)}")

        # each cum only has one acknowledgement option with no effects
        super(Cum, self).generate_immediate_effect()

        self.add_debug_line(f"{DEBUG_LOG_SCOPES} = {YES}")

    def generate_options(self):
        option = self.options[0]
        with Block(self, OPTION):
            self.add_line(f"{NAME} = {option.fullname}")
            if option.tooltip is not None:
                self.add_line(f"{CUSTOM_TOOLTIP} = {option.fullname}.tt")


class Sex(Event):
    def __init__(self, *args, stam_cost_1: float = 0, stam_cost_2: float = 0, **kwargs):
        self.stam_cost_1 = stam_cost_1
        self.stam_cost_2 = stam_cost_2
        super(Sex, self).__init__(*args, **kwargs)
        assert isinstance(self.id, EventsSex)

    def generate_desc(self):
        self.generate_incoming_options_desc()

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

        super(Sex, self).generate_desc()

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
                elif option.category == OptionCategory.CUM:
                    self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")
                else:
                    raise RuntimeError(f"Unsupported option category {option.category}")

    def generate_sub_option_effect(self, option):
        self.generate_hidden_opinion_change_effect(option.subdom_sub)
        with Block(self, SAVE_SCOPE_VALUE_AS):
            self.add_line(f"{NAME} = {SEX_TRANSITION}")
            self.add_line(f"{VALUE} = {option.id}")
        self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")

    def generate_dom_option_effect(self, option, sub_options):
        with Block(self, IF):
            with Block(self, LIMIT):
                self.add_line(f"{DOM_SUCCESS} = {YES}")
            self.generate_hidden_opinion_change_effect(option.subdom_dom_success)
            with Block(self, SAVE_SCOPE_VALUE_AS):
                self.add_line(f"{NAME} = {SEX_TRANSITION}")
                self.add_line(f"{VALUE} = {option.id}")
            self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")
        with Block(self, ELSE):
            self.generate_hidden_opinion_change_effect(option.subdom_dom_fail)
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


class EventMap:
    def __init__(self):
        self.events: typing.Dict[EventId, Event] = {}

    def add(self, event: Event):
        self.events[event.id] = event

    def __getitem__(self, event_id: EventId):
        return self.events[event_id]

    def all(self):
        return self.events.values()


def link_events_and_options(events: EventMap):
    options = {}
    option_id = 1
    for e in events.all():
        for o in e.options:
            o.id = option_id
            option_id += 1
            o.from_id = e.id
            # option generate fullname
            o.fullname = f"{OPTION_NAMESPACE}.{o.id}"
            if o.next_id is not None:
                o.next_event = events[o.next_id]
                o.from_event = e
                o.next_event.incoming_options.append(o)
            options[o.id] = o
    return options


# TODO validate events (no disconnected events; have at least some in-edge or out-edge)
def generate_strings(events, options):
    # generate localizations
    # event require maps because there are different files needed for each type of event
    event_text = {}
    event_localization = {}
    for event in events.all():
        ns = event_type_namespace(event.id)
        if ns not in event_text:
            event_text[ns] = [EVENTS_FILE_HEADER,
                              f"{NAMESPACE} = {ns}"]
            event_localization[ns] = [L_ENGLISH, EVENTS_FILE_HEADER]
        event_text[ns].append(str(event))
        event_localization[ns].append(event.generate_localization())
    # options are all grouped together into a single file so no need for a map
    option_localization = [L_ENGLISH]
    for option in options.values():
        option_localization.append(option.generate_localization())
    option_localization = "\n".join(option_localization)
    return event_text, event_localization, option_localization


def export_strings(event_text, event_localization, option_localization, dry_run=False):
    event_ns_to_file_map = {
        FIRST_NAMESPACE: "events/LIDA_first_events.txt",
        SEX_NAMESPACE  : "events/LIDA_sex_events.txt",
        CUM_NAMESPACE  : "events/LIDA_cum_events.txt",
    }
    event_ns_to_localization_map = {
        FIRST_NAMESPACE: "localization/english/LIDA_first_events_l_english.yml",
        SEX_NAMESPACE  : "localization/english/LIDA_sex_events_l_english.yml",
        CUM_NAMESPACE  : "localization/english/LIDA_cum_events_l_english.yml",
    }
    for ns in event_text.keys():
        event_file = event_ns_to_file_map[ns]
        localization_file = event_ns_to_localization_map[ns]
        event_str = "\n".join(event_text[ns])
        localization_str = "\n".join(event_localization[ns])
        print(f"Exporting event text to {event_file}")
        print(f"Exporting event localization to {localization_file}")
        if dry_run:
            print(event_str)
            print(localization_str)
        else:
            with open(event_file, "w", encoding='utf-8') as f:
                f.write(UTF8_BOM)
                f.write(event_str)
            with open(localization_file, "w", encoding='utf-8') as f:
                f.write(UTF8_BOM)
                f.write(localization_str)

    localization_file = "localization/english/LIDA_options_l_english.yml"
    print(f"Exporting options localization to {localization_file}")
    if dry_run:
        print(option_localization)
    else:
        with open(localization_file, "w", encoding='utf-8') as f:
            f.write(UTF8_BOM)
            f.write(option_localization)


parser = argparse.ArgumentParser(
    description='Generate CK3 Dynamic Affairs events and localization',
)
parser.add_argument('-d', '--dry', action='store_true',
                    help="dry run printing the generated strings without exporting to file")
args = parser.parse_args()

if __name__ == "__main__":
    es = EventMap()
    # define directed graph of events
    es.add(Sex(EventsSex.HANDJOB_TEASE, "Handjob Tease",
               stam_cost_1=0, stam_cost_2=1,
               desc=f"""With a knowing smirk, you size {THEM} up and put both your hands on their chest.
                    Leveraging your weight, you push and trap him against a wall. You slide your knee up his leg 
                    and play with his bulge. 
                    
                    "Is that a dagger in your pocket, or are you glad to see me?"
                    
                    Tracing your fingers against thin fabric, you work your way up above his trouser before 
                    pulling down to free his member. It twitches at the brisk air and the sharp contrast in 
                    sensation against your warm hands.""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Jerk him off",
                          "You're too turned on to be satisfied with just jerking him off"
                          ),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth"),
               )))
    es.add(Sex(EventsSex.HANDJOB, "Handjob",
               stam_cost_1=0, stam_cost_2=1,
               desc=f"""handjob desc""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Continue jerking him off",
                          "You're too turned on to be satisfied with just jerking him off"),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth"),
                   Option(EventsCum.HANDJOB_CUM_IN_HAND, OptionCategory.CUM,
                          "Milk him into your soft palms"
                          )
               )))
    es.add(Sex(EventsSex.ASS_TEASE, "Ass Tease",
               stam_cost_1=1, stam_cost_2=1,
               desc=f"""ass tease desc""",
               options=(
                   Option(EventsSex.ASS_TEASE, OptionCategory.DOM,
                          "Continue teasing him with your ass",
                          "You have better uses for that hard cock than just teasing it"),
                   Option(EventsCum.ASS_TEASE_CUM_ON_ASS, OptionCategory.CUM,
                          "Have him coat your ass with his seed")
               )))
    es.add(Sex(EventsSex.BLOWJOB_DOM, "Dom Blowjob",
               stam_cost_1=0.5, stam_cost_2=1,
               desc=f"""dom blowjob desc""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Deny him your mouth, replacing it with your hands",
                          "The potent musk of his member, inflated by the proximity of your nose to his"
                          "pubes, strangely captivates you and you lose this opportunity to assert more dominance."),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.DOM,
                          "Continue milking his cock with your lips and tongue",
                          "The incessant invasion of his member down your mouth pussy momentarily puts you in a trance"
                          ", leaving the initiative in his hands.",
                          subdom_dom_success=0),
                   Option(EventsCum.BLOWJOB_CUM_IN_MOUTH_DOM, OptionCategory.CUM,
                          "Milk him dry onto your tongue"),
                   Option(EventsCum.BLOWJOB_CUM_ON_FACE, OptionCategory.CUM,
                          "Make him coat your face in cum"),
                   Option(EventsCum.BLOWJOB_RUINED_ORGASM, OptionCategory.CUM,
                          "Cruelly deny him his release")
               )))
    es.add(Cum(EventsCum.HANDJOB_CUM_IN_HAND, "A Cumshot in Hand is Worth Two in the Bush",
               subdom_change=1,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe your hands on a nearby cloth"),
               desc=f"""cum in hand desc"""
               ))
    es.add(Cum(EventsCum.ASS_TEASE_CUM_ON_ASS, "Icing on the Cake",
               subdom_change=0,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean yourself and get dressed"),
               desc=f"""cum on ass desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_CUM_ON_FACE, "Painting your Face",
               subdom_change=-2,
               terminal_option=Option(None, OptionCategory.OTHER, "Sample some of the stray globs of cum"),
               desc=f"""cum on face desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_CUM_IN_MOUTH_DOM, "Satisfying your Sweet Tooth",
               subdom_change=-1,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe away any cum that might've escaped"),
               desc=f"""cum in mouth dom desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_RUINED_ORGASM, "A Firm Grasp on His Release",
               subdom_change=2,
               terminal_option=Option(None, OptionCategory.OTHER, "Leave him yearning and frustrated"),
               desc=f"""blowjob ruined orgasm desc"""
               ))

    # find/specify all source sex events, which are ones which have at most themselves as input events
    all_options = link_events_and_options(es)
    # TODO plot directed graph of events and options
    export_strings(*generate_strings(es, all_options), dry_run=args.dry)
