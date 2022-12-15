import enum
import typing
import argparse
import subprocess
import re

UTF8_BOM = u'\ufeff'
debug = True


class EventsFirst(enum.Enum):
    MEETING_WITH_SPOUSE = 1


class EventsSex(enum.Enum):
    HANDJOB_TEASE = 1
    ASS_TEASE = 2
    HANDJOB = 3
    BLOWJOB_DOM = 4
    STANDING_FUCKED_FROM_BEHIND = 5
    BLOWJOB_SUB = 6
    DEEPTHROAT = 7


class EventsCum(enum.Enum):
    HANDJOB_CUM_IN_HAND = 1
    BLOWJOB_CUM_IN_MOUTH_DOM = 2
    BLOWJOB_CUM_IN_MOUTH_SUB = 6
    BLOWJOB_CUM_ON_FACE = 3
    BLOWJOB_RUINED_ORGASM = 4
    ASS_TEASE_CUM_ON_ASS = 5


# alias for any event type
EventId = typing.Union[EventsFirst, EventsSex, EventsCum]

# common keywords (avoid and catch typos)
SCOPE = "scope"
VAR = "var"
MODIFIER = "modifier"
DESC = "desc"
TRIGGER = "trigger"
SHOW_AS_UNAVAILABLE = "show_as_unavailable"
ANIMATION = "animation"
FIRST_VALID = "first_valid"
TRIGGERED_DESC = "triggered_desc"
LEFT_PORTRAIT = "left_portrait"
RIGHT_PORTRAIT = "right_portrait"
IMMEDIATE = "immediate"
OPTION = "option"
AFTER = "after"
TARGET = "target"
OPINION = "opinion"
TITLE = "title"
THEME = "theme"
TYPE = "type"
NAME = "name"
VALUE = "value"
CUSTOM_TOOLTIP = "custom_tooltip"
ADD = "add"

CHARACTER_EVENT = "character_event"
CHARACTER = "character"

DOMINANT_OPINION = "dominant_opinion"
ROOT = "root"
AFFAIRS_PARTNER = "scope:affairs_partner"

ROOT_STAMINA = "scope:root_stamina"
PARTNER_STAMINA = "scope:partner_stamina"
DOM_CHANCE = "dom_chance"
DOM_SUCCESS = "dom_success"
THIS_DOM_CHANCE = "this_dom_chance"
DOM_SUCCESS_ADJUSTMENT = "dom_success_adjustment"
DOM_ATTEMPT_TOOLTIP = "attempt_dom_tooltip"
DOM_NO_SUB_TOOLTIP = "dom_no_sub_tooltip"
VOLUNTARY_SUB_TOOLTIP = "voluntary_sub_tooltip"
DOM_SUCCESS_ADJUSTMENT_TOOLTIP = "dom_success_adjustment_tooltip"

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
HAS_VARIABLE = "has_variable"
NOT = "NOT"
OR = "OR"
AND = "AND"
IS_FEMALE = "is_female"
CHECK_IF_ROOT_CUM_EFFECT = "check_if_root_cum_effect"
CLEAR_ROOT_CUM_EFFCT = "clear_root_cum_effect"
ROOT_CUM = "root_cum"

SELECT_START_AFFAIRS_EFFECT = "select_start_affairs_effect"
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
SAVE_TEMPORARY_SCOPE_VALUE_AS = "save_temporary_scope_value_as"
RANDOM = "random"
RANDOM_LIST = "random_list"

DEBUG_LOG_SCOPES = "debug_log_scopes"

SEX_TRANSITION = "sex_transition"
DOM_TRANSITION = "dom_transition"
SUB_TRANSITION = "sub_transition"
CUM_TRANSITION = "cum_transition"
PREV_EVENT = "prev_event"

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
base_event_weight = 5
max_options_per_type = 2


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


class BlockRoot:
    def __init__(self):
        # temporary data when generating the string representation
        self._lines = []
        self.indent = 0

    def add_line(self, text: str):
        self._lines.append("\t" * self.indent + text)

    def add_comment(self, text: str):
        self.add_line("# " + text)

    def add_debug_line(self, *args):
        if debug:
            self.add_line(*args)

    def add_debug_comment(self, *args):
        if debug:
            self.add_comment(*args)

    def clear(self):
        self._lines = []

    def __repr__(self):
        return "\n".join(self._lines)


class Event(BlockRoot):
    """Vertices in a scene graph, each corresponding to a specific scene"""

    def __init__(self, eid: EventId, title, desc="placeholder event desc", theme="seduction",
                 animation_left="flirtation", animation_right="flirtation_left", options=(),
                 root_female=True,
                 # text for if the root cums; None indicates the default root cum text will be used
                 root_cum_text=None,
                 # custom generation functions, these take the event as teh first argument and call add_line
                 custom_desc: typing.Optional[typing.Callable] = None,
                 custom_immediate_effect: typing.Optional[typing.Callable] = None):
        self.id = eid
        self.title = title
        self.desc = clean_str(desc)
        self.theme = theme
        self.anim_l = animation_left
        self.anim_r = animation_right

        self.root_cum_text = root_cum_text
        if self.root_cum_text is not None:
            self.root_cum_text = clean_str(self.root_cum_text) + "\\n"

        namespace = event_type_namespace(self.id)
        eid = self.id.value
        self.fullname = f"{namespace}.{eid}"

        self.options: typing.Sequence[Option] = options
        # to be computed in a backwards pass to see what options come into this event
        self.incoming_options = []
        # for an incoming event, its options not going directly to this option
        # their dom failure could potentially lead to this event, so we need that in our description
        self.adjacent_options = []

        self.custom_desc = custom_desc
        self.custom_localization = None
        self.custom_immediate_effect = custom_immediate_effect

        self.root_female = root_female
        super(Event, self).__init__()

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
                self.add_line(f"{ANIMATION} = {self.anim_r}")

            with Block(self, DESC):
                self.generate_desc()
            with Block(self, IMMEDIATE):
                self.generate_immediate_effect()

            self.generate_options()

        return "\n".join(self._lines)

    def save_scope_value_as(self, name, value):
        with Block(self, SAVE_SCOPE_VALUE_AS):
            self.add_line(f"{NAME} = {name}")
            self.add_line(f"{VALUE} = {value}")

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
        if self.root_cum_text is not None:
            lines.append(f"{self.fullname}.{ROOT_CUM}: \"{self.root_cum_text}\"")
        if self.custom_localization is not None:
            lines.append(self.custom_localization)
        return "\n".join(lines)

    def generate_root_cum_desc(self):
        prefix = "f" if self.root_female else "rm"
        with Block(self, TRIGGERED_DESC):
            with Block(self, TRIGGER):
                self.add_line(f"{SCOPE}:{ROOT_CUM} = {YES}")
                # depending on if we have a special root cum text or if we need to default
            if self.root_cum_text is not None:
                self.add_line(f"{DESC} = {self.fullname}.{ROOT_CUM}")
            else:
                self.add_line(f"{DESC} = {ROOT_CUM}_{prefix}")

    def generate_incoming_options_desc(self):
        # description of the transition from the previous event
        # populate the reverse graph to see what options come into this event
        if len(self.incoming_options) == 0:
            return
        with Block(self, FIRST_VALID):
            for option in self.incoming_options:
                with Block(self, TRIGGERED_DESC):
                    with Block(self, TRIGGER):
                        self.add_line(f"{EXISTS} = {SCOPE}:{SEX_TRANSITION}")
                        self.add_line(f"{SCOPE}:{SEX_TRANSITION} = {option.id}")
                    self.add_debug_comment(option.from_event.title)
                    self.add_debug_comment(option.transition_text)
                    self.add_line(f"{DESC} = {SEX_TRANSITION}_{option.id}")
            for option in self.adjacent_options:
                if option.failed_transition_text != "":
                    with Block(self, TRIGGERED_DESC):
                        with Block(self, TRIGGER):
                            self.add_line(f"{EXISTS} = {SCOPE}:{SEX_TRANSITION}")
                            self.add_line(f"{SCOPE}:{SEX_TRANSITION} = {option.id + dom_fail_offset}")
                        self.add_debug_comment(f"{option} failed")
                        self.add_debug_comment(option.failed_transition_text)
                        self.add_line(f"{DESC} = {SEX_TRANSITION}_{option.id + dom_fail_offset}")

        # if we failed a dom transition and this event has a direct option from that failed event, use it
        # for all the incoming options
        for option in self.incoming_options:
            with Block(self, TRIGGERED_DESC):
                with Block(self, TRIGGER):
                    self.add_line(f"{EXISTS} = {SCOPE}:{SEX_TRANSITION}")
                    self.add_line(f"{SCOPE}:{SEX_TRANSITION} > {dom_fail_offset}")
                    self.add_line(f"{EXISTS} = {SCOPE}:{PREV_EVENT}")
                    self.add_line(f"{SCOPE}:{PREV_EVENT} = {option.from_id.value}")
                # TODO consider replacing the whole sex_transition system with just PREV_EVENT
                self.add_debug_comment(f"defaulted to {option}")
                self.add_line(f"{DESC} = {SEX_TRANSITION}_{option.id}")


class OptionCategory(enum.IntEnum):
    SUB = 1
    DOM = 2
    CUM = 3
    OTHER = 4


def clean_str(string):
    return re.sub(' +', ' ', string.strip().replace('\n', '')).replace('\\n\\n ', '\\n\\n')


class Option:
    """Directed edges in a scene graph, going from one event to another (or terminating)"""

    def __init__(self, next_id: typing.Optional[EventId], category: OptionCategory, option_text: str,
                 transition_text: str = "",
                 # for dom options, have a chance to fail them
                 failed_transition_text="",
                 weight: int = 10, tooltip=None,
                 # for dom options, specify the opinion change on success and failure of dom
                 subdom_dom_success=1, subdom_dom_fail=-2,
                 # for sub options, specify the opinion change on sub choice
                 subdom_sub=-1,
                 # for dom options, different options may be easier or harder than the base chance
                 dom_success_adjustment=0,
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
        self.option_text = option_text
        self.transition_text = clean_str(transition_text) + "\\n"
        self.failed_transition_text = clean_str(failed_transition_text)
        if self.failed_transition_text != "":
            self.failed_transition_text += "\\n"
        self.tooltip = tooltip

        self.subdom_dom_success = subdom_dom_success
        self.subdom_dom_fail = subdom_dom_fail
        self.subdom_sub = subdom_sub

        self.dom_success_adjustment = dom_success_adjustment

        self.modifiers = modifiers
        self.triggers = triggers

    def __repr__(self):
        return f"{self.id}: {self.from_id} -> {self.next_id}"

    def generate_modifiers_and_triggers(self, event: Event):
        for modifier in self.modifiers:
            event.add_line(f"{MODIFIER} = {{ {modifier} }}")
        for trigger in self.triggers:
            event.add_line(f"{TRIGGER} = {{ {trigger} }}")

    def generate_localization(self):
        lines = [f"{self.fullname}: \"{self.option_text}\"",
                 f"{SEX_TRANSITION}_{self.id}: \"{self.transition_text}\"",
                 f"{SEX_TRANSITION}_{self.id + dom_fail_offset}: \"{self.failed_transition_text}\""]
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
        self.generate_root_cum_desc()
        super(Cum, self).generate_desc()

    def generate_immediate_effect(self):
        self.add_line(f"{CHECK_IF_ROOT_CUM_EFFECT} = {YES}")
        # register that we have had sex to compute consequences
        if self.subdom_change != 0:
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
    def __init__(self, *args,
                 stam_cost_1: float = 0, stam_cost_2: float = 0, **kwargs):
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

        for prefix, value_to_check in [(first_prefix, ROOT_STAMINA), (second_prefix, PARTNER_STAMINA)]:
            with Block(self, FIRST_VALID):
                # if you cum, then no need to indicate your sexual stamina, instead fill it with the root cum text
                if value_to_check == ROOT_STAMINA:
                    self.generate_root_cum_desc()
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
        choice = 0
        for choice in range(min(len(options_list), max_options_per_type)):
            with Block(self, RANDOM_LIST):
                for option in options_list:
                    self.add_debug_comment(option.next_id.name)
                    with Block(self, f"{option.weight}"):
                        option.generate_modifiers_and_triggers(self)
                        # choose without replacement
                        for prev_choice in range(choice):
                            with Block(self, TRIGGER):
                                with Block(self, NOT):
                                    self.add_line(f"{SCOPE}:{option_transition_str}_{prev_choice} = {option.id}")
                        with Block(self, f"{SAVE_SCOPE_VALUE_AS}"):
                            self.add_line(f"{NAME} = {option_transition_str}_{choice}")
                            self.add_line(f"{VALUE} = {option.id}")
        # fill in the rest of the choices so we don't have to check if it exists
        for choice in range(choice + 1, max_options_per_type):
            self.save_scope_value_as(f"{option_transition_str}_{choice}", -1)

    def generate_immediate_effect(self):
        with Block(self, LIDA_ONGOING_SEX_EFFECT):
            self.add_line(f"{STAMINA_COST_1} = {self.stam_cost_1}")
            self.add_line(f"{STAMINA_COST_2} = {self.stam_cost_2}")

        # for each event, allow for special description on root cum; if none specified, default one will be used
        self.add_line(f"{CHECK_IF_ROOT_CUM_EFFECT} = {YES}")
        # separate into categories; within each category the outcome of which option gets selected is random
        categories_to_options = {c: [] for c in OptionCategory}
        for option in self.options:
            categories_to_options[option.category].append(option)

        if len(categories_to_options[OptionCategory.SUB]) == 0:
            self.add_comment("enforce dom success if we have no sub options to ensure there is at least a valid option")
            self.save_scope_value_as(DOM_CHANCE, 100)
            self.save_scope_value_as(DOM_SUCCESS, 0)
        else:
            # calculate the success probability
            self.add_line(f"{CALCULATE_DOM_SUCCESS_EFFECT} = {YES}")

        # roll for both the dom and sub transitions
        for c, c_trans in [(OptionCategory.DOM, DOM_TRANSITION), (OptionCategory.SUB, SUB_TRANSITION)]:
            self.generate_options_transition(categories_to_options[c], c_trans)

        # additionally if there are cumming actions allow for these options
        options_list = categories_to_options[OptionCategory.CUM]
        if len(options_list) > 0:
            with Block(self, IF):
                with Block(self, LIMIT):
                    self.add_line(f"{PARTNER_STAMINA} <= 0")
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
                self.add_debug_comment(str(option))
                self.add_line(f"{NAME} = {option.fullname}")
                if option.tooltip is not None:
                    self.add_line(f"{CUSTOM_TOOLTIP} = {option.fullname}.tt")

                # for some reason show_as_unavailable is not a subset of trigger, so have to duplicate it
                for block in [TRIGGER, SHOW_AS_UNAVAILABLE]:
                    with Block(self, block):
                        # cumming locks you out of any dom transitions, but only if there are some sub options to transition to
                        if block == TRIGGER and option.category == OptionCategory.DOM and len(
                                categories_to_options[OptionCategory.SUB]) > 0:
                            self.add_line(f"{NOT} = {{ {SCOPE}:{ROOT_CUM} = {YES} }}")
                        if option.category in [OptionCategory.DOM, OptionCategory.SUB]:
                            trans_type = DOM_TRANSITION if option.category == OptionCategory.DOM else SUB_TRANSITION
                            self.add_line(f"{NOT} = {{ {EXISTS} = {SCOPE}:{CUM_TRANSITION}_0 }}")
                            with Block(self, OR):
                                # TODO possible problem if a previous event has more options than this one
                                for choice in range(max_options_per_type):
                                    self.add_line(f"{SCOPE}:{trans_type}_{choice} = {option.id}")
                        elif option.category == OptionCategory.CUM:
                            with Block(self, OR):
                                for choice in range(max_options_per_type):
                                    with Block(self, AND):
                                        self.add_line(f"{EXISTS} = {SCOPE}:{CUM_TRANSITION}_{choice}")
                                        self.add_line(f"{SCOPE}:{CUM_TRANSITION}_{choice} = {option.id}")

                # save this event
                with Block(self, SAVE_SCOPE_VALUE_AS):
                    self.add_line(f"{NAME} = {PREV_EVENT}")
                    self.add_line(f"{VALUE} = {self.id.value}")
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
        self.add_line(f"{CUSTOM_TOOLTIP} = {VOLUNTARY_SUB_TOOLTIP}")
        self.generate_hidden_opinion_change_effect(option.subdom_sub)
        with Block(self, SAVE_SCOPE_VALUE_AS):
            self.add_line(f"{NAME} = {SEX_TRANSITION}")
            self.add_line(f"{VALUE} = {option.id}")
        self.add_line(f"{TRIGGER_EVENT} = {option.next_event.fullname}")

    def generate_dom_option_effect(self, option, sub_options):
        if len(sub_options) == 0:
            self.add_line(f"{CUSTOM_TOOLTIP} = {DOM_NO_SUB_TOOLTIP}")
        else:
            self.add_line(f"{CUSTOM_TOOLTIP} = {DOM_ATTEMPT_TOOLTIP}")
            if option.dom_success_adjustment != 0:
                self.save_scope_value_as(DOM_SUCCESS_ADJUSTMENT, option.dom_success_adjustment)
                self.add_line(f"{CUSTOM_TOOLTIP} = {DOM_SUCCESS_ADJUSTMENT_TOOLTIP}")

        # each dom option has potentially different success offsets
        with Block(self, SAVE_TEMPORARY_SCOPE_VALUE_AS):
            self.add_line(f"{NAME} = {THIS_DOM_CHANCE}")
            with Block(self, VALUE):
                self.add_line(f"{ADD} = {SCOPE}:{DOM_CHANCE}")
                # this allows dom_success_adjustment to also be a scripted value (e.g. check if you're a blowjob expert)
                self.add_line(f"{ADD} = {option.dom_success_adjustment}")
        with Block(self, IF):
            with Block(self, LIMIT):
                self.add_line(f"{SCOPE}:{DOM_SUCCESS} <= {SCOPE}:{THIS_DOM_CHANCE}")
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
                        self.add_line(f"{SCOPE}:{SUB_TRANSITION}_0 = {sub_option.id}")
                    self.add_line(f"{TRIGGER_EVENT} = {sub_option.next_event.fullname}")


class Block:
    """Context manager for nesting blocks of = {} with proper indentation"""

    def __init__(self, event: BlockRoot, left_hand_side: str):
        self.event = event
        self.event.add_line(f"{left_hand_side} = {{")

    def __enter__(self):
        self.event.indent += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.event.indent -= 1
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
    for e in events.all():
        for o in e.incoming_options:
            for ao in o.from_event.options:
                if ao.category == OptionCategory.DOM and ao not in e.adjacent_options:
                    e.adjacent_options.append(ao)
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
    # organize effects into effects for randomly selecting them initially
    b = BlockRoot()
    # find sex events that have at most just itself as the incoming event
    source_events = []
    for e in events.all():
        is_source = True
        for o in e.incoming_options:
            ie = o.from_event
            if ie != e and not isinstance(ie.id, EventsFirst):
                is_source = False
                break
        if is_source:
            source_events.append(e)
    with Block(b, SELECT_START_AFFAIRS_EFFECT):
        with Block(b, RANDOM_LIST):
            for e in source_events:
                with Block(b, str(base_event_weight)):
                    # triggers on these based on if root is female
                    with Block(b, TRIGGER):
                        b.add_line(f"{IS_FEMALE} = {yes_no(e.root_female)}")
                    # TODO modifier on fetishes and sub/domness (needs to be added to the events as well)
                    b.add_comment(e.title)
                    b.add_line(f"{TRIGGER_EVENT} = {e.fullname}")
    effect_text = str(b)
    return event_text, effect_text, event_localization, option_localization


def export_strings(event_text, effect_text, event_localization, option_localization, dry_run=False):
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
    effect_file = "common/scripted_effects/LIDA_generated_effects.txt"
    print(f"Exporting effects to {effect_file}")
    if dry_run:
        print(effect_text)
    else:
        with open(effect_file, "w", encoding='utf-8') as f:
            f.write(UTF8_BOM)
            f.write(EVENTS_FILE_HEADER)
            f.write("\n")
            f.write(effect_text)


def export_dot_graphviz(events, horizontal=True, censored=False):
    gv_filename = "vis.gv"
    with open(gv_filename, "w") as f:
        f.write("digraph G {\n")
        if horizontal:
            f.write("rankdir=LR;\n")
        f.write("fontname=Helvetica;\n")

        # sex events
        for event in events.all():
            if isinstance(event.id, EventsSex):
                f.write(event.id.name)
                f.write(f"[fontname=Helvetica, shape=box, "
                        f"label={event.id.value if censored else event.id.name}]")
                f.write(";\n")
                for option in event.options:
                    # terminal option
                    if option.next_id is None:
                        continue
                    f.write(f"{event.id.name} -> {option.next_id.name}")
                    attr = []
                    if option.category == OptionCategory.DOM:
                        attr.append("color=red")
                    elif option.category == OptionCategory.SUB:
                        attr.append("color=blue")

                    attr.append(f"penwidth={option.weight / 5}")

                    if len(attr) > 0:
                        attr = "[" + ",".join(attr) + "]"
                        f.write(attr)
                    f.write(";\n")

        # cum events (sink nodes)
        f.write("subgraph cluster_cum {\n label=\"Terminal Events\";\n rank=sink;\n")
        for event in events.all():
            if isinstance(event.id, EventsCum):
                f.write(event.id.name)
                f.write(
                    f"[fontname=Helvetica, shape=box, style=filled, rank=sink, color=\"#f2f0ae\", "
                    f"label={event.id.value if censored else event.id.name}]")
        f.write("}\n")
        f.write("}\n")

    subprocess.run(["dot", "-Tpng", gv_filename, "-o", "vis.png"])


parser = argparse.ArgumentParser(
    description='Generate CK3 Dynamic Affairs events and localization',
)
parser.add_argument('-d', '--dry', action='store_true',
                    help="dry run printing the generated strings without exporting to file")
args = parser.parse_args()


def define_events(es: EventMap):
    # define directed graph of events
    # TODO instead of sampling dom success/fail, just sample a number then do the comparison ourselves
    # TODO since some dom options may be easier than others
    es.add(Sex(EventsSex.HANDJOB_TEASE, "Handjob Tease",
               stam_cost_1=0, stam_cost_2=1,
               desc=f"""With a knowing smirk, you size {THEM} up and put both your hands on their chest.
                    Leveraging your weight, you push and trap him against a wall. You slide your knee up his leg 
                    and play with his bulge. 
                    \\n\\n
                    "Is that a dagger in your pocket, or are you glad to see me?"
                    \\n\\n
                    Tracing your fingers against thin fabric, you work your way up above his trouser before 
                    pulling down to free his member. It twitches at the brisk air and the sharp contrast in 
                    sensation against your warm hands.""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Jerk him off",
                          transition_text="Your continue building a rhythm going up and down his shaft with your hands.",
                          failed_transition_text="You're too turned on to be satisfied with just jerking him off."),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          They start moving a hand to place behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.HANDJOB, "Handjob",
               stam_cost_1=0, stam_cost_2=1,
               desc=f"""handjob desc""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Continue jerking him off",
                          transition_text=f"""
                          Under the interminable strokes from your hand, {THEM}'s cock has 
                          fully hardened. Dew-like pre dribbles from the tip, lubricating the whole shaft.""",
                          failed_transition_text="You're too turned on to be satisfied with just jerking him off"),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          They start moving a hand to place behind your head, but you swat it away."""),
                   Option(EventsCum.HANDJOB_CUM_IN_HAND, OptionCategory.CUM,
                          "Milk him into your soft palms", )
               )))
    es.add(Sex(EventsSex.ASS_TEASE, "Ass Tease",
               stam_cost_1=1, stam_cost_2=2,
               desc=f"""ass tease desc""",
               options=(
                   Option(EventsSex.ASS_TEASE, OptionCategory.DOM,
                          "Continue teasing him with your ass",
                          transition_text=f"""
                          You continue to rub his rod in between your buns. You can feel a coolness
                          from {THEM}'s pre, slicking up your back. The contrast with the rhythmic thrusts from his 
                          hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it"),
                   Option(EventsCum.ASS_TEASE_CUM_ON_ASS, OptionCategory.CUM,
                          "Have him coat your ass with his seed")
               )))
    es.add(Sex(EventsSex.BLOWJOB_DOM, "Dom Blowjob",
               stam_cost_1=0.5, stam_cost_2=2,
               desc=f"""dom blowjob desc""",
               options=(
                   Option(EventsSex.HANDJOB, OptionCategory.DOM,
                          "Deny him your mouth, replacing it with your hands",
                          weight=5,
                          transition_text=f"""
                          You give {THEM}'s head a last lick, making sure to drag it out as if expressing your tongue's
                          reluctance to part from it. You replace the warmth of your mouth with the milder warmth of
                          your palms, and replace the bobbing of your head with strokes from your hands.
                          """,
                          failed_transition_text=f"""
                          The potent musk of his member, inflated by the proximity of your 
                          nose to his pubes, strangely captivates you and you lose this opportunity to assert more 
                          dominance."""),
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.DOM,
                          "Continue milking his cock with your lips and tongue",
                          transition_text=f"""
                          You continue to bob your head back and forth, occasionally glancing up and making adjustments
                          based on their expression. The fact that you have total control over {THEM}'s pleasure makes
                          you excited.""",
                          failed_transition_text=f"""
                          The incessant invasion of his member down your throat
                          momentarily puts you in a trance, leaving the initiative in his hands.""",
                          subdom_dom_success=0),
                   Option(EventsSex.BLOWJOB_SUB, OptionCategory.SUB,
                          "Let him do the work of thrusting in and out of your mouth",
                          transition_text=f"""
                          Your jaw and neck sore from doing all the work, you decide to let him
                          do pick up the slack. "Come on {THEM}, show me your mettle."
                          \\n\\n
                          Instead of wasting words, he places both hands behind your head and starts thrusting."""),
                   # TODO make these options more likely if you are addicted to cum
                   Option(EventsCum.BLOWJOB_CUM_IN_MOUTH_DOM, OptionCategory.CUM,
                          "Milk him dry onto your tongue", weight=3),
                   Option(EventsCum.BLOWJOB_CUM_ON_FACE, OptionCategory.CUM,
                          "Make him coat your face in cum", weight=3),
                   Option(EventsCum.BLOWJOB_RUINED_ORGASM, OptionCategory.CUM,
                          "Cruelly deny him his release")
               )))
    es.add(Sex(EventsSex.BLOWJOB_SUB, "Sub Blowjob",
               stam_cost_1=1.0, stam_cost_2=1.5,
               desc=f"""
               sub blowjob desc""",
               options=(
                   Option(EventsSex.BLOWJOB_DOM, OptionCategory.DOM,
                          "Take back control and be the active one giving the blowjob",
                          transition_text=f"""
                          Putting both hands on his waist, you curb his thrusts. 
                          {THEM} moves his arms as if to protest, but your licks along his shaft
                          resolve any nascent objections.""",
                          failed_transition_text=f"""
                          Putting both hands on his waist, you attempt to curb his thrusts.
                          However, on your knees beneath him, you don't have enough leverage to forcefully
                          stop him and he seems to have no intention of letting you back in control.
                          """),
                   Option(EventsSex.BLOWJOB_SUB, OptionCategory.SUB,
                          "Let him continue his thrusts",
                          transition_text=f"""
                          You adjust your posture better suit his thrusts, making sure to pull away your teeth."""),
                   Option(EventsSex.DEEPTHROAT, OptionCategory.SUB,
                          "Let him thrust even deeper",
                          transition_text=f"""
                          He takes advantage of your lack of strong resistance to dominate your mouth
                          further. Trapping your head with his hands, he plunges deeper while you gag."""),
                   Option(EventsCum.BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.CUM,
                          "Let him cum in your mouth"),
                   Option(EventsCum.BLOWJOB_CUM_ON_FACE, OptionCategory.CUM,
                          "Make him coat your face in cum"),
               )))
    es.add(Sex(EventsSex.DEEPTHROAT, "Deepthroat",
               stam_cost_1=1.0, stam_cost_2=2.0,
               desc=f"""
               deepthroat desc""",
               options=(
                   Option(EventsSex.BLOWJOB_SUB, OptionCategory.DOM,
                          "Take some control back",
                          transition_text=f"""
                          Putting both hands on his waist, you reduce his thrusts to a manageable pace and depth. 
                          """,
                          failed_transition_text=f"""
                          Putting both hands on his waist, you push and try to stop his thrusts.
                          It's all in vain, however, as he ignores you.
                          """),
                   Option(EventsSex.DEEPTHROAT, OptionCategory.SUB,
                          "Continue deepthroating",
                          transition_text=f"""
                          He continues fucking your throat while 
                          your vision blurs against a mixture of tears, saliva, and sex juices."""),
                   Option(EventsCum.BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.CUM,
                          "He cums in your mouth"),
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
    # TODO add chance of acquiring fetishes
    es.add(Cum(EventsCum.BLOWJOB_CUM_ON_FACE, "Painting your Face",
               subdom_change=-2,
               terminal_option=Option(None, OptionCategory.OTHER, "Sample some stray globs of cum"),
               desc=f"""cum on face desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_CUM_IN_MOUTH_DOM, "Satisfying your Sweet Tooth",
               subdom_change=-1,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe away any cum that might've escaped"),
               desc=f"""cum in mouth dom desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_CUM_IN_MOUTH_SUB, "Down the Gullet",
               subdom_change=-2,
               terminal_option=Option(None, OptionCategory.OTHER, "Recover from having your throat used so roughly"),
               desc=f"""cum in mouth sub desc"""
               ))
    es.add(Cum(EventsCum.BLOWJOB_RUINED_ORGASM, "A Firm Grasp on His Release",
               subdom_change=2,
               terminal_option=Option(None, OptionCategory.OTHER, "Leave him yearning and frustrated"),
               desc=f"""blowjob ruined orgasm desc"""
               ))


if __name__ == "__main__":
    es = EventMap()
    define_events(es)

    # find/specify all source sex events, which are ones which have at most themselves as input events
    all_options = link_events_and_options(es)
    # plot directed graph of events and options (graphviz)
    export_dot_graphviz(es)
    export_strings(*generate_strings(es, all_options), dry_run=args.dry)
