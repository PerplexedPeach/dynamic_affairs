import enum
import typing
import argparse
import subprocess
import re

UTF8_BOM = u'\ufeff'
debug = True


class EventsFirst(enum.Enum):
    MEETING_WITH_SPOUSE = 1
    MEETING_WITH_SPOUSE_INITIAL = 2
    MEETING_WITH_VASSAL = 3
    MEETING_WITH_VASSAL_INITIAL = 4
    MEETING_WITH_LIEGE = 5
    MEETING_WITH_LIEGE_INITIAL = 6
    MEETING_WITH_PRISONER = 7
    MEETING_WITH_PRISONER_INITIAL = 8
    MEETING_WITH_ACQUAINTANCE = 9
    MEETING_WITH_ACQUAINTANCE_INITIAL = 10


class EventsSex(enum.Enum):
    FM_HANDJOB_TEASE = 1
    FM_ASS_TEASE = 2
    FM_HANDJOB = 3
    FM_BLOWJOB_DOM = 4
    FM_STANDING_FUCKED_FROM_BEHIND = 5
    FM_BLOWJOB_SUB = 6
    FM_DEEPTHROAT = 7
    FM_HOTDOG = 8
    FM_STANDING_FINGERED_FROM_BEHIND = 9
    FM_ASS_RUB = 10
    FM_REVERSE_COWGIRL = 11
    FM_COWGIRL = 12
    FM_MISSIONARY = 13
    FM_PRONE_BONE = 14


class EventsCum(enum.Enum):
    FM_HANDJOB_CUM_IN_HAND = 1
    FM_BLOWJOB_CUM_IN_MOUTH_DOM = 2
    FM_BLOWJOB_CUM_IN_MOUTH_SUB = 6
    FM_BLOWJOB_CUM_ON_FACE = 3
    FM_RUINED_ORGASM = 4
    FM_ASS_TEASE_CUM_ON_ASS = 5
    FM_CUM_ON_GROIN = 12
    FM_PULL_OUT_CUM_ON_ASS = 7
    FM_CREAMPIE_REGULAR = 8
    FM_CREAMPIE_ON_TOP = 9
    FM_CREAMPIE_BRED = 10
    FM_CREAMPIE_KEEP = 11


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
CUSTOM_DESCRIPTION = "custom_description"
TEXT = "text"
ADD = "add"
IS_SPOUSE_OF = "is_spouse_of"
IS_IN_LIST = "is_in_list"
REVERSE_HAS_OPINION_MODIFIER = "reverse_has_opinion_modifier"
EVERY_PRISONER = "every_prisoner"
ADD_TO_TEMPORARY_LIST = "add_to_temporary_list"
IS_VASSAL_OR_BELOW_OF = "is_vassal_or_below_of"
TARGET_IS_VASSAL_OR_BELOW = "target_is_vassal_or_below"
ADD_INTERNAL_FLAG = "add_internal_flag"
SPECIAL = "special"
DANGEROUS = "dangerous"
ADD_CHARACTER_MODIFIER = "add_character_modifier"
YEARS = "years"

CHARACTER_EVENT = "character_event"
CHARACTER = "character"

DOMINANT_OPINION = "dominant_opinion"
AFFAIR_SPURNED_OPINION = "affair_spurned_opinion"
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
CANCEL_MEETING_OPTION = "cancel_meeting_option"
CANCEL_MEETING_TOOLTIP = "cancel_meeting_tooltip"
CANT_DOM_DUE_TO_CUM_TOOLTIP = "cant_dom_due_to_cum_tooltip"

# effects
TRIGGER_EVENT = "trigger_event"
IF = "if"
ELSE_IF = "else_if"
LIMIT = "limit"
ELSE = "else"
HIDDEN_EFFECT = "hidden_effect"
REVERSE_ADD_OPINION = "reverse_add_opinion"
CALCULATE_DOM_SUCCESS_EFFECT = "calculate_dom_success_effect"
STORE_SUBDOM_VALUE_EFFECT = "store_subdom_value_effect"
SUBDOM = "subdom"
YES = "yes"
NO = "no"
EXISTS = "exists"
HAS_VARIABLE = "has_variable"
HAS_TRAIT = "has_trait"
NOT = "NOT"
OR = "OR"
AND = "AND"
IS_FEMALE = "is_female"
CHECK_IF_ROOT_CUM_EFFECT = "check_if_root_cum_effect"
CLEAR_ROOT_CUM_EFFCT = "clear_root_cum_effect"
ROOT_CUM = "root_cum"
OVERRIDE_BACKGROUND = "override_background"
EVENT_BACKGROUND = "event_background"
LOCALE = "locale"

BECOME_MORE_SUB_EFFECT = "become_more_sub_effect"
BECOME_MORE_DOM_EFFECT = "become_more_dom_effect"
SELECT_START_AFFAIRS_EFFECT = "select_start_affairs_effect"
SELECT_RANDOM_SEX_SOURCE_EFFECT = "select_random_sex_source_effect"
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
PREGNANCY_CHANCE = 30  # basic value  replaced base value with 30 because it was doing weird stuff otherwise
STRESS_EFFECTS = "STRESS_EFFECTS"
DRAMA = "DRAMA"

SAVE_SCOPE_VALUE_AS = "save_scope_value_as"
SAVE_TEMPORARY_SCOPE_VALUE_AS = "save_temporary_scope_value_as"
RANDOM = "random"
RANDOM_LIST = "random_list"
CHANCE = "chance"

DEBUG_LOG_SCOPES = "debug_log_scopes"

SEX_TRANSITION = "sex_transition"
DOM_TRANSITION = "dom_transition"
SUB_TRANSITION = "sub_transition"
CUM_TRANSITION = "cum_transition"
FIRST_TRANSITION = "first_transition"
PREV_EVENT = "prev_event"

NAMESPACE = "namespace"
OPTION_NAMESPACE = "LIDAoption"
FIRST_NAMESPACE = "LIDAf"
SEX_NAMESPACE = "LIDAs"
CUM_NAMESPACE = "LIDAc"
UNIMPLEMENTED_PAIRING_EVENT = "LIDA.3"

L_ENGLISH = "l_english:"
EVENTS_FILE_HEADER = "# GENERATED FILE - DO NOT MODIFY DIRECTLY"

# traits
LIDA_SUB = "lida_sub"
LIDA_DOM = "lida_dom"

# localization constants
THEM = "[affairs_partner.GetFirstName]"
ME_FULL_REGNAL = "[ROOT.Char.GetFullNameRegnal]"
ME_NAME = "[ROOT.Char.GetFirstName]"
ME_LADY_LORD = "[ROOT.Char.GetLadyLord]"  # Idk how to get this to just take the first title (Baroness/Duchess/Queen/etc.)

dom_fail_offset = 10000
base_event_weight = 5
max_options_per_type = 2
FEMALE = "f"
MALE = "m"

# Outfit tags
OUTFIT_TAGS = "outfit_tags"
TRIGGERED_OUTFIT = "triggered_outfit"
NO_CLOTHES = "no_clothes"
# outfit scope values
ROOT_NAKED = "root_naked"
PARTNER_NAKED = "partner_naked"

# animation tags
KNEEL_2 = "throne_room_kneel_2"
KNEEL_RULER_3 = "throne_room_ruler_3"
BOW = "throne_room_bow_1"
BOW_3 = "throne_room_bow_3"
PRISON_HOUSE = "prisonhouse"
BEG = "beg"
BOREDOM = "boredom"
DISGUST = "disgust"
DISMISSAL = "dismissal"
ECSTASY = "ecstasy"
LOVE = "love"
SHAME = "shame"
SHOCK = "shock"
SCHEME = "scheme"
SCHADENFREUDE = "schadenfreude"
SADNESS = "sadness"
WORRY = "worry"
PERSONALITY_BOLD = "personality_bold"
PERSONALITY_CONTENT = "personality_content"
WRITER = "throne_room_writer"
IDLE = "idle"
FLIRTATION = "flirtation"
FLIRTATION_LEFT = "flirtation_left"
HAPPINESS = "happiness"
PREGNANT = "pregnant"
PERSONALITY_IRRATIONAL = "personality_irrational"
WAR_ATTACKER = "war_attacker"
WAR_OVER_WIN = "war_over_win"
WAR_OVER_LOSE = "war_over_lose"
CHESS_COCKY = "chess_cocky"
CHESS_CERTAIN_WIN = "chess_certain_win"
FEAR = "fear"
EYEROLL = "eyeroll"

# modifiers
SEXUALLY_FRUSTRATED = "sexually_frustrated"
WEARING_CUMMY_CLOTHING = "wearing_cummy_clothing"


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

    def assign(self, name, value):
        self.add_line(f"{name} = {value}")

    def save_scope_value_as(self, name, value):
        with Block(self, SAVE_SCOPE_VALUE_AS):
            self.assign(NAME, name)
            self.assign(VALUE, value)

    def __repr__(self):
        return "\n".join(self._lines)


class Effect:
    def __call__(self, b: BlockRoot):
        pass


class Event(BlockRoot):
    """Vertices in a scene graph, each corresponding to a specific scene"""

    def __init__(self, eid: EventId, title, desc="placeholder event desc", theme="seduction",
                 animation_left=FLIRTATION, animation_right=FLIRTATION_LEFT, options=(),
                 root_gender=FEMALE,
                 partner_gender=MALE,
                 # whether this event removes their clothes
                 root_removes_clothes=False,
                 partner_removes_clothes=False,
                 # text for if the root cums; None indicates the default root cum text will be used
                 root_cum_text=None,
                 # custom generation functions, these take the event as teh first argument and call add_line
                 custom_desc: typing.Optional[typing.Callable] = None,
                 # chance for this event to rank up dom/sub (always opposite, but in a separate roll for the partner)
                 root_become_more_sub_chance=0, root_become_more_dom_chance=0,
                 custom_immediate_effect: typing.Optional[Effect] = None):
        self.id = eid
        self.title = title
        if isinstance(desc, str):
            desc = Desc(desc)
        self.desc = desc
        self.theme = theme
        self.anim_l = animation_left
        self.anim_r = animation_right

        self.root_become_more_sub_chance = root_become_more_sub_chance
        self.root_become_more_dom_chance = root_become_more_dom_chance

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

        self.root_gender = root_gender
        self.partner_gender = partner_gender

        self.root_removes_clothes = root_removes_clothes
        self.partner_removes_clothes = partner_removes_clothes
        super(Event, self).__init__()

    def __repr__(self):
        """Turn the event into a self string; will be called sequentially on the events to generate them"""
        self._lines = []
        with Block(self, self.fullname):
            self.add_comment(f"{self.id.name}: {self.title}")
            self.assign(TYPE, CHARACTER_EVENT)
            self.assign(TITLE, f"{self.fullname}.t")
            self.assign(THEME, self.theme)
            self.generate_background()
            with Block(self, LEFT_PORTRAIT):
                self.assign(CHARACTER, ROOT)
                self.assign(ANIMATION, self.anim_l)
                self.generate_root_outfit()

            with Block(self, RIGHT_PORTRAIT):
                self.assign(CHARACTER, AFFAIRS_PARTNER)
                self.assign(ANIMATION, self.anim_r)
                self.generate_partner_outfit()

            with Block(self, DESC):
                self.generate_desc()
            with Block(self, IMMEDIATE):
                self.generate_immediate_effect()

            self.generate_options()

        return "\n".join(self._lines)

    def generate_root_outfit(self):
        with Block(self, TRIGGERED_OUTFIT):
            with Block(self, TRIGGER):
                self.assign(EXISTS, f"{SCOPE}:{ROOT_NAKED}")
            # TODO add triggered outfits such as depending on traits / collars / piercings and so on
            with Block(self, OUTFIT_TAGS):
                self.add_line(NO_CLOTHES)

    def generate_partner_outfit(self):
        with Block(self, TRIGGERED_OUTFIT):
            with Block(self, TRIGGER):
                self.assign(EXISTS, f"{SCOPE}:{PARTNER_NAKED}")
            with Block(self, OUTFIT_TAGS):
                self.add_line(NO_CLOTHES)

    def generate_desc(self):
        self.desc.generate_desc(self)
        if self.custom_desc is not None:
            # calling the custom desc will modify the event string text in place, and return a localization string
            self.custom_localization = self.custom_desc(self)

    def _generate_change_subdom_trait(self, chance, root_change, partner_change):
        if chance > 0:
            with Block(self, RANDOM):
                self.assign(CHANCE, chance)
                self.assign(root_change, YES)
            with Block(self, AFFAIRS_PARTNER):
                with Block(self, RANDOM):
                    self.assign(CHANCE, chance)
                    self.assign(partner_change, YES)

    def generate_immediate_effect(self):
        self._generate_change_subdom_trait(self.root_become_more_sub_chance, BECOME_MORE_SUB_EFFECT,
                                           BECOME_MORE_DOM_EFFECT)
        self._generate_change_subdom_trait(self.root_become_more_dom_chance, BECOME_MORE_DOM_EFFECT,
                                           BECOME_MORE_SUB_EFFECT)

        if self.root_removes_clothes:
            self.save_scope_value_as(ROOT_NAKED, YES)
        if self.partner_removes_clothes:
            self.save_scope_value_as(PARTNER_NAKED, YES)

        if self.custom_immediate_effect is not None:
            self.custom_immediate_effect(self)

    def generate_options(self):
        pass

    def generate_hidden_opinion_change_effect(self, change):
        with Block(self, CHANGE_SUBDOM_EFFECT):
            self.assign(CHANGE, change)

    def generate_options_transition(self, options_list, option_transition_str):
        if len(options_list) == 0:
            return
        for choice in range(min(len(options_list), max_options_per_type)):
            with Block(self, RANDOM_LIST):
                for option in options_list:
                    self.add_debug_comment(option.next_id.name)
                    with Block(self, f"{option.weight}"):
                        option.generate_modifiers_and_triggers(self)
                        with Block(self, TRIGGER):
                            # depending on this transition leads to cumming or not
                            if isinstance(option.next_id, EventsCum):
                                self.add_line(f"{PARTNER_STAMINA} <= 0")
                            else:
                                self.add_line(f"{PARTNER_STAMINA} > 0")
                            # choose without replacement to avoid duplicating the prev choices
                            for prev_choice in range(choice):
                                with Block(self, NOT):
                                    self.assign(f"{SCOPE}:{option_transition_str}_{prev_choice}", option.id)
                        self.save_scope_value_as(f"{option_transition_str}_{choice}", option.id)
        # fill in the rest of the choices so we don't have to check if it exists
        for choice in range(1, max_options_per_type):
            with Block(self, IF):
                with Block(self, LIMIT):
                    with Block(self, NOT):
                        self.assign(EXISTS, f"{SCOPE}:{option_transition_str}_{choice}")
                self.save_scope_value_as(f"{option_transition_str}_{choice}", -1)

    def generate_localization(self):
        lines = [f"{self.fullname}.t: \"{self.title}\"", self.desc.generate_localization(self)]
        if self.root_cum_text is not None:
            lines.append(f"{self.fullname}.{ROOT_CUM}: \"{self.root_cum_text}\"")
        if self.custom_localization is not None:
            lines.append(self.custom_localization)
        return "\n".join(lines)

    POSSIBLE_BACKGROUNDS = ["battlefield", "alley_night", "alley_day", "temple", "corridor_night", "corridor_day",
                            "courtyard", "dungeon", "docks", "feast", "market", "tavern", "throne_room", "garden",
                            "gallows", "bedchamber", "study", "council_chamber", "sitting_room"]

    def generate_background(self):
        for background in self.POSSIBLE_BACKGROUNDS:
            with Block(self, OVERRIDE_BACKGROUND):
                with Block(self, TRIGGER):
                    self.assign(f"{SCOPE}:{LOCALE}", f"flag:{background}")
                self.assign(EVENT_BACKGROUND, background)

    def generate_root_cum_desc(self):
        prefix = self.root_gender
        with Block(self, TRIGGERED_DESC):
            with Block(self, TRIGGER):
                self.assign(f"{SCOPE}:{ROOT_CUM}", YES)
                # depending on if we have a special root cum text or if we need to default
            if self.root_cum_text is not None:
                self.assign(DESC, f"{self.fullname}.{ROOT_CUM}")
            else:
                self.assign(DESC, f"{ROOT_CUM}_{prefix}")

    def generate_incoming_options_desc(self):
        # description of the transition from the previous event
        # populate the reverse graph to see what options come into this event
        sex_incoming_options = [o for o in self.incoming_options if isinstance(o.from_id, EventsSex)]
        if len(sex_incoming_options) == 0:
            return
        with Block(self, FIRST_VALID):
            for option in sex_incoming_options:
                if option.transition_text is None:
                    continue
                with Block(self, TRIGGERED_DESC):
                    with Block(self, TRIGGER):
                        self.assign(EXISTS, f"{SCOPE}:{SEX_TRANSITION}")
                        self.assign(f"{SCOPE}:{SEX_TRANSITION}", option.id)
                    self.add_debug_comment(option.from_event.title)
                    self.add_debug_comment(option.transition_text.desc)
                    option.transition_text.generate_desc(self, option)
            for option in self.adjacent_options:
                if option.failed_transition_text is None:
                    continue
                with Block(self, TRIGGERED_DESC):
                    with Block(self, TRIGGER):
                        self.assign(EXISTS, f"{SCOPE}:{SEX_TRANSITION}")
                        self.assign(f"{SCOPE}:{SEX_TRANSITION}", option.id + dom_fail_offset)
                    self.add_debug_comment(f"{option} failed")
                    self.add_debug_comment(option.failed_transition_text.desc)
                    option.failed_transition_text.generate_desc(self, option)

        # if we failed a dom transition and this event has a direct option from that failed event, use it
        # for all the incoming options
        for option in sex_incoming_options:
            if option.transition_text is None:
                continue
            with Block(self, TRIGGERED_DESC):
                with Block(self, TRIGGER):
                    self.assign(EXISTS, f"{SCOPE}:{SEX_TRANSITION}")
                    self.add_line(f"{SCOPE}:{SEX_TRANSITION} > {dom_fail_offset}")
                    self.assign(EXISTS, f"{SCOPE}:{PREV_EVENT}")
                    self.assign(f"{SCOPE}:{PREV_EVENT}", option.from_id.value)
                # TODO consider replacing the whole sex_transition system with just PREV_EVENT
                self.add_debug_comment(f"defaulted to {option}")
                option.transition_text.generate_desc(self, option)


class OptionCategory(enum.IntEnum):
    SUB = 1
    DOM = 2
    OTHER = 3


def clean_str(string):
    return re.sub(' +', ' ', string.strip().replace('\n', '')).replace('\\n\\n ', '\\n\\n')


class Option:
    """Directed edges in a scene graph, going from one event to another (or terminating)"""

    def __init__(self, next_id: typing.Optional[EventId], category: OptionCategory, option_text: str,
                 transition_text=None,
                 # for dom options, have a chance to fail them
                 failed_transition_text=None,
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
        if isinstance(transition_text, str):
            transition_text = Desc(transition_text)
            transition_text.desc += "\\n"
        self.transition_text: Desc = transition_text
        self.failed_transition_text = None
        if failed_transition_text is not None:
            if isinstance(failed_transition_text, str):
                failed_transition_text = Desc(failed_transition_text)
                failed_transition_text.desc += "\\n"
            self.failed_transition_text: Desc = failed_transition_text
            self.failed_transition_text.subid = dom_fail_offset

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
            event.assign(MODIFIER, f"{{ {modifier} }}")
        for trigger in self.triggers:
            event.assign(TRIGGER, f"{{ {trigger} }}")

    def generate_localization(self):
        lines = [f"{self.fullname}: \"{self.option_text}\""]
        if self.transition_text is not None:
            lines.append(self.transition_text.generate_localization(self))
        if self.failed_transition_text is not None:
            lines.append(self.failed_transition_text.generate_localization(self))
        if self.tooltip is not None:
            lines.append(f"{self.fullname}.tt: \"{self.tooltip}\"")

        return "\n".join(lines)


Describable = typing.Union[Event, Option]


class Desc:
    def __init__(self, desc, subid=0):
        self.desc = clean_str(desc)
        self.subid = subid

    def generate_desc(self, b: Event, o: typing.Optional[Option] = None):
        if o is not None:
            self._generate_desc_option(b, o)
        else:
            self._generate_desc_event(b)

    def generate_localization(self, b: Describable):
        if isinstance(b, Event):
            return self._generate_localization_event(b)
        elif isinstance(b, Option):
            return self._generate_localization_option(b)

    def _generate_desc_event(self, b: Event):
        b.assign(DESC, f"{b.fullname}.{DESC}.{self.subid}")

    def _generate_localization_event(self, b: Event):
        return f"{b.fullname}.{DESC}.{self.subid}: \"{self.desc}\""

    def _generate_desc_option(self, b: Event, o: Option):
        b.assign(DESC, f"{SEX_TRANSITION}_{o.id}.{self.subid}")

    def _generate_localization_option(self, b: Option):
        return f"{SEX_TRANSITION}_{b.id}.{self.subid}: \"{self.desc}\""


class TriggeredDesc(Desc):
    def __init__(self, trigger_condition, desc):
        self.trigger_condition = trigger_condition
        super(TriggeredDesc, self).__init__(desc)

    def generate_desc(self, b: Event, o: typing.Optional[Option] = None):
        with Block(b, TRIGGERED_DESC):
            with Block(b, TRIGGER):
                b.add_line(self.trigger_condition)
            super(TriggeredDesc, self).generate_desc(b, o)


class ComposedDesc(Desc):
    def __init__(self, *descs: typing.Union[Desc, str]):
        self.descs = [d if isinstance(d, Desc) else Desc(d) for d in descs]
        for i, d in enumerate(self.descs):
            d.subid = i
        super(ComposedDesc, self).__init__("")

    def generate_desc(self, b: Event, o: typing.Optional[Option] = None):
        for desc in self.descs:
            desc.generate_desc(b, o)

    def generate_localization(self, b: Describable):
        return "\n".join([d.generate_localization(b) for d in self.descs])


class Cum(Event):
    def __init__(self, *args, terminal_option: Option, preg_chance_1: typing.Union[float, str] = 0,
                 preg_chance_2: typing.Union[float, str] = 0,
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
            self.assign(CHARACTER_1, ROOT)
            self.assign(CHARACTER_2, AFFAIRS_PARTNER)
            self.assign(C1_PREGNANCY_CHANCE, self.preg_chance_1)
            self.assign(C2_PREGNANCY_CHANCE, self.preg_chance_2)
            self.assign(STRESS_EFFECTS, yes_no(self.stress_effects))
            self.assign(DRAMA, yes_no(self.drama))

        # each cum only has one acknowledgement option with no effects
        super(Cum, self).generate_immediate_effect()

        self.add_debug_line(f"{DEBUG_LOG_SCOPES} = {YES}")

    def generate_options(self):
        option = self.options[0]
        with Block(self, OPTION):
            self.assign(NAME, option.fullname)
            if option.tooltip is not None:
                self.assign(CUSTOM_TOOLTIP, f"{option.fullname}.tt")


class First(Event):
    def __init__(self, *args, background="sitting_room", source_sex_events=(), **kwargs):
        if background not in self.POSSIBLE_BACKGROUNDS:
            raise RuntimeError(f"{background} not in possible backgrounds list")
        self.background = background
        # generate options to each sex source event
        options = []
        for event in source_sex_events:
            options.append(Option(event.id, OptionCategory.OTHER, event.title))

        super(First, self).__init__(*args, options=options, **kwargs)

    def generate_immediate_effect(self):
        # save to use for all future events
        self.save_scope_value_as(LOCALE, f"flag:{self.background}")
        # sample which option to use
        self.generate_options_transition(self.options, FIRST_TRANSITION)
        super(First, self).generate_immediate_effect()

    def generate_options(self):
        for option in self.options:
            with Block(self, OPTION):
                self.add_debug_comment(str(option))
                self.assign(NAME, option.fullname)
                if option.tooltip is not None:
                    self.assign(CUSTOM_TOOLTIP, f"{option.fullname}.tt")

                with Block(self, TRIGGER):
                    with Block(self, OR):
                        for choice in range(max_options_per_type):
                            self.assign(f"{SCOPE}:{FIRST_TRANSITION}_{choice}", option.id)

                # save this event
                self.save_scope_value_as(PREV_EVENT, self.id.value)
                self.save_scope_value_as(SEX_TRANSITION, option.id)
                self.assign(TRIGGER_EVENT, option.next_event.fullname)
        # last option is to back out
        with Block(self, OPTION):
            self.assign(NAME, CANCEL_MEETING_OPTION)
            self.assign(CUSTOM_TOOLTIP, CANCEL_MEETING_TOOLTIP)
            with Block(self, REVERSE_ADD_OPINION):
                self.assign(MODIFIER, AFFAIR_SPURNED_OPINION)
                self.assign(TARGET, AFFAIRS_PARTNER)


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
        first_prefix = self.root_gender
        second_prefix = f"p{self.partner_gender}"

        for prefix, value_to_check in [(first_prefix, ROOT_STAMINA), (second_prefix, PARTNER_STAMINA)]:
            with Block(self, FIRST_VALID):
                # if you cum, then no need to indicate your sexual stamina, instead fill it with the root cum text
                if value_to_check == ROOT_STAMINA:
                    self.generate_root_cum_desc()
                for threshold, suffix in stamina_thresholds.items():
                    with Block(self, TRIGGERED_DESC):
                        with Block(self, TRIGGER):
                            self.add_line(f"{value_to_check} < {threshold}")
                        self.assign(DESC, f"{prefix}_{suffix}_stam")
                # backup option for high stamina
                self.assign(DESC, f"{prefix}_high_stam")

        super(Sex, self).generate_desc()

    def generate_immediate_effect(self):
        with Block(self, LIDA_ONGOING_SEX_EFFECT):
            self.assign(STAMINA_COST_1, self.stam_cost_1)
            self.assign(STAMINA_COST_2, self.stam_cost_2)

        # for each event, allow for special description on root cum; if none specified, default one will be used
        self.assign(CHECK_IF_ROOT_CUM_EFFECT, YES)
        # separate into categories; within each category the outcome of which option gets selected is random
        categories_to_options = {c: [] for c in OptionCategory}
        for option in self.options:
            categories_to_options[option.category].append(option)

        self.assign(STORE_SUBDOM_VALUE_EFFECT, YES)
        selectable_non_cum_sub_options = [o for o in categories_to_options[OptionCategory.SUB] if
                                          isinstance(o.next_id, EventsSex)]
        if len(selectable_non_cum_sub_options) == 0:
            self.add_comment("enforce dom success if we have no sub options to ensure there is at least a valid option")
            self.save_scope_value_as(DOM_CHANCE, 100)
            self.save_scope_value_as(DOM_SUCCESS, 0)
        else:
            # calculate the success probability
            self.assign(CALCULATE_DOM_SUCCESS_EFFECT, YES)

        # roll for both the dom and sub transitions
        for c, c_trans in [(OptionCategory.DOM, DOM_TRANSITION), (OptionCategory.SUB, SUB_TRANSITION)]:
            self.generate_options_transition(categories_to_options[c], c_trans)

        super(Sex, self).generate_immediate_effect()

        self.add_debug_line(f"{DEBUG_LOG_SCOPES} = {YES}")

    def generate_options(self):
        categories_to_options = {c: [] for c in OptionCategory}
        for option in self.options:
            categories_to_options[option.category].append(option)

        for option in self.options:
            with Block(self, OPTION):
                self.add_debug_comment(str(option))
                self.assign(NAME, option.fullname)
                if option.tooltip is not None:
                    self.assign(CUSTOM_TOOLTIP, f"{option.fullname}.tt")

                # for some reason show_as_unavailable is not a subset of trigger, so have to duplicate it
                with Block(self, TRIGGER):
                    if option.category in [OptionCategory.DOM, OptionCategory.SUB]:
                        # non-cum options are only available if partner is not cumming
                        if not isinstance(option.next_id, EventsCum):
                            self.add_line(f"{PARTNER_STAMINA} > 0")
                        trans_type = DOM_TRANSITION if option.category == OptionCategory.DOM else SUB_TRANSITION
                        with Block(self, OR):
                            for choice in range(max_options_per_type):
                                self.assign(f"{SCOPE}:{trans_type}_{choice}", option.id)

                # save this event
                self.save_scope_value_as(PREV_EVENT, self.id.value)
                # for dom options, it could backfire and get you more dommed
                if option.category == OptionCategory.DOM:
                    self.generate_dom_option_effect(option, categories_to_options[OptionCategory.SUB])
                    # cumming decreases dom success
                    with Block(self, IF):
                        with Block(self, LIMIT):
                            self.assign(f"{SCOPE}:{ROOT_CUM}", YES)
                        self.assign(CUSTOM_TOOLTIP, CANT_DOM_DUE_TO_CUM_TOOLTIP)
                        self.assign(ADD_INTERNAL_FLAG, DANGEROUS)
                elif option.category == OptionCategory.SUB:
                    self.generate_sub_option_effect(option)
                else:
                    raise RuntimeError(f"Unsupported option category {option.category}")

    def generate_sub_option_effect(self, option):
        self.assign(CUSTOM_TOOLTIP, VOLUNTARY_SUB_TOOLTIP)
        self.generate_hidden_opinion_change_effect(option.subdom_sub)
        self.save_scope_value_as(SEX_TRANSITION, option.id)
        self.assign(TRIGGER_EVENT, option.next_event.fullname)

    def generate_dom_option_effect(self, option, sub_options):
        if len(sub_options) == 0:
            self.assign(CUSTOM_TOOLTIP, DOM_NO_SUB_TOOLTIP)
        else:
            self.assign(CUSTOM_TOOLTIP, DOM_ATTEMPT_TOOLTIP)
            if option.dom_success_adjustment != 0:
                self.save_scope_value_as(DOM_SUCCESS_ADJUSTMENT, option.dom_success_adjustment)
                self.assign(CUSTOM_TOOLTIP, DOM_SUCCESS_ADJUSTMENT_TOOLTIP)

        # each dom option has potentially different success offsets
        with Block(self, SAVE_TEMPORARY_SCOPE_VALUE_AS):
            self.assign(NAME, THIS_DOM_CHANCE)
            with Block(self, VALUE):
                self.assign(ADD, f"{SCOPE}:{DOM_CHANCE}")
                # this allows dom_success_adjustment to also be a scripted value (e.g. check if you're a blowjob expert)
                self.assign(ADD, option.dom_success_adjustment)
        with Block(self, IF):
            with Block(self, LIMIT):
                self.add_line(f"{SCOPE}:{DOM_SUCCESS} <= {SCOPE}:{THIS_DOM_CHANCE}")
            self.generate_hidden_opinion_change_effect(option.subdom_dom_success)
            self.save_scope_value_as(SEX_TRANSITION, option.id)
            self.assign(TRIGGER_EVENT, option.next_event.fullname)
        with Block(self, ELSE):
            self.generate_hidden_opinion_change_effect(option.subdom_dom_fail)
            # register that we've failed to dom (use a large offset plus that ID)
            self.save_scope_value_as(SEX_TRANSITION, option.id + dom_fail_offset)
            # for each possible sub transition check if we've sampled that
            for sub_option in sub_options:
                with Block(self, IF):
                    with Block(self, LIMIT):
                        self.assign(f"{SCOPE}:{SUB_TRANSITION}_0", sub_option.id)
                    self.assign(TRIGGER_EVENT, sub_option.next_event.fullname)


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
        if event.id in self.events:
            raise RuntimeError(f"Trying to re-add {event.id}")
        self.events[event.id] = event

    def __getitem__(self, event_id: EventId):
        return self.events[event_id]

    def all(self):
        return self.events.values()


def link_events_and_options(events: EventMap):
    options = {}
    option_id = 1
    # clear some lists to enable recalling this
    for e in events.all():
        e.incoming_options = []
        e.adjacent_options = []
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
            if not isinstance(o.from_id, EventsSex):
                continue
            for ao in o.from_event.options:
                if ao.category == OptionCategory.DOM and ao not in e.adjacent_options:
                    e.adjacent_options.append(ao)
    return options


def get_source_sex_events(events: EventMap):
    source_events = []
    for e in events.all():
        if not isinstance(e.id, EventsSex):
            continue
        is_source = True
        for o in e.incoming_options:
            ie = o.from_event
            if ie != e and not isinstance(ie.id, EventsFirst):
                is_source = False
                break
        if is_source:
            source_events.append(e)
    return source_events


def limit_has_opinion(b: BlockRoot):
    with Block(b, LIMIT):
        with Block(b, REVERSE_HAS_OPINION_MODIFIER):
            b.assign(TARGET, AFFAIRS_PARTNER)
            b.assign(MODIFIER, DOMINANT_OPINION)


def add_meeting_events(b: BlockRoot, es, id_initial, id_repeat):
    with Block(b, IF):
        limit_has_opinion(b)
        b.add_comment(id_repeat.name)
        b.assign(TRIGGER_EVENT, es[id_repeat].fullname)
    with Block(b, ELSE):
        b.add_comment(id_initial.name)
        b.assign(TRIGGER_EVENT, es[id_initial].fullname)


def inside_limit_check_gender(b: BlockRoot, root_gender, partner_gender):
    b.assign(IS_FEMALE, yes_no(root_gender == FEMALE))
    with Block(b, AFFAIRS_PARTNER):
        b.assign(IS_FEMALE, yes_no(partner_gender == FEMALE))


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
    with Block(b, SELECT_START_AFFAIRS_EFFECT):
        # depending on various conditions, choose different first events to launch
        prisoner_list = "prisoner_list"
        with Block(b, EVERY_PRISONER):
            b.assign(ADD_TO_TEMPORARY_LIST, prisoner_list)
        # F/M events
        with Block(b, IF):
            with Block(b, LIMIT):
                b.assign(IS_SPOUSE_OF, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, es, EventsFirst.MEETING_WITH_SPOUSE_INITIAL, EventsFirst.MEETING_WITH_SPOUSE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_IN_LIST, prisoner_list)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, es, EventsFirst.MEETING_WITH_PRISONER_INITIAL, EventsFirst.MEETING_WITH_PRISONER)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_VASSAL_OR_BELOW_OF, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, es, EventsFirst.MEETING_WITH_LIEGE_INITIAL, EventsFirst.MEETING_WITH_LIEGE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(TARGET_IS_VASSAL_OR_BELOW, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, es, EventsFirst.MEETING_WITH_VASSAL_INITIAL, EventsFirst.MEETING_WITH_VASSAL)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, es, EventsFirst.MEETING_WITH_ACQUAINTANCE_INITIAL,
                               EventsFirst.MEETING_WITH_ACQUAINTANCE)
        # TODO M/F events and other pairings
        with Block(b, ELSE):
            b.assign(TRIGGER_EVENT, UNIMPLEMENTED_PAIRING_EVENT)

    # generate sex source effect to allow directly randomly transitioning into a sex event
    with Block(b, SELECT_RANDOM_SEX_SOURCE_EFFECT):
        with Block(b, RANDOM_LIST):
            for event in get_source_sex_events(events):
                with Block(b, "100"):
                    with Block(b, TRIGGER):
                        inside_limit_check_gender(b, event.root_gender, event.partner_gender)
                    b.assign(TRIGGER_EVENT, event.fullname)

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


def export_dot_graphviz(events, horizontal=True, censored=False, show_titles=True):
    def get_event_name(event):
        name = event.id.name
        if show_titles:
            name += f"\\n{event.title}"
        if censored:
            name = event.id.value
        return name

    def get_event_attr(event, fontname="Helvetica", shape="box", style="filled", rank=None):
        attr = [f"fontname={fontname}", f"shape={shape}", f"style={style}", f"label=\"{get_event_name(event)}\""]
        if rank is not None:
            attr.append(f"rank={rank}")
        if event.root_become_more_dom_chance > 0:
            attr.append(f"fillcolor=\"0.0 {float(event.root_become_more_dom_chance) / 100} 1.0\"")
        elif event.root_become_more_sub_chance > 0:
            attr.append(f"fillcolor=\"0.6 {float(event.root_become_more_sub_chance) / 100} 1.0\"")
        else:
            attr.append(f"fillcolor=\"#ffffff\"")
        attr = "[" + ",".join(attr) + "]"
        return attr

    gv_filename = "vis.gv"
    with open(gv_filename, "w") as f:
        f.write("digraph G {\n")
        if horizontal:
            f.write("rankdir=LR;\n")
        f.write("fontname=Helvetica;\n")
        # merge edges going back and forth - not good since we need different colors
        # f.write("concentrate=true;\n")
        f.write("compound=true;\n")

        # organize events into gender pairings
        pairings = [(FEMALE, MALE), (MALE, FEMALE), (FEMALE, FEMALE), (MALE, MALE)]
        for pairing in pairings:
            these_events = EventMap()
            for event in events.all():
                if event.root_gender == pairing[0] and event.partner_gender == pairing[1]:
                    these_events.add(event)

            if len(these_events.events) == 0:
                continue

            f.write(
                f"subgraph cluster_{pairing[0]}{pairing[1]} "
                f"{{\n label=\"{pairing[0].upper()}/{pairing[1].upper()} Events\";\n")
            # f.write("style=filled;\n fillcolor=\"#f2f0ae\";\n")

            source_sex_events = get_source_sex_events(events)
            cum_events = []
            regular_sex_events = []
            first_events = []
            for event in events.all():
                if event in source_sex_events:
                    continue
                if isinstance(event.id, EventsCum):
                    cum_events.append(event)
                elif isinstance(event.id, EventsFirst):
                    first_events.append(event)
                else:
                    regular_sex_events.append(event)
            events_with_options = source_sex_events + regular_sex_events

            # regular sex events
            for event in regular_sex_events:
                f.write(event.id.name)
                f.write(get_event_attr(event))
                f.write(";\n")

            # sex source events (source nodes)
            f.write("subgraph cluster_sex_source {\n label=\"Source\";\n rank=same;\n")
            # invisible node for others to connect to the cluster as a whole
            for i, event in enumerate(source_sex_events):
                f.write(event.id.name)
                f.write(get_event_attr(event))
                f.write(";\n")
            f.write("}\n")

            f.write("subgraph cluster_meeting {\n label=\"Start Meeting Events\";\n rank=source;\n")
            f.write("style=filled;\n fillcolor=\"#A5FFC7\";\n")
            for i, event in enumerate(first_events):
                f.write(event.id.name)
                f.write(get_event_attr(event))
                f.write(";\n")
                # create visual connection between the start meeting events and the source events
                if i == len(first_events) // 2:
                    other = source_sex_events[len(source_sex_events) // 2]
                    f.write(f"{event.id.name} -> {other.id.name} [ltail=cluster_meeting,lhead=cluster_sex_source];\n")
            f.write("}\n")

            # cum events (sink nodes)
            f.write("subgraph cluster_cum {\n label=\"Terminal Events\";\n rank=sink;\n")
            f.write("style=filled;\n fillcolor=\"#f2f0ae\";\n")
            for event in cum_events:
                f.write(event.id.name)
                f.write(get_event_attr(event, rank="sink"))
                f.write(";\n")
            f.write("}\n")

            for event in events_with_options:
                for option in event.options:
                    # terminal option
                    if option.next_id is None:
                        continue
                    f.write(f"{event.id.name} -> {option.next_id.name}")
                    attr = []
                    if option.category == OptionCategory.DOM:
                        attr.append("color=red")
                    elif option.category == OptionCategory.SUB and option.subdom_sub < 0:
                        attr.append("color=blue")

                    attr.append(f"penwidth={option.weight / 5}")

                    if len(attr) > 0:
                        attr = "[" + ",".join(attr) + "]"
                        f.write(attr)
                    f.write(";\n")

            f.write("}\n")

        f.write("}\n")

    subprocess.run(["dot", "-Tpng", gv_filename, "-o", "vis.png"])


parser = argparse.ArgumentParser(
    description='Generate CK3 Dynamic Affairs events and localization',
)
parser.add_argument('-d', '--dry', action='store_true',
                    help="dry run printing the generated strings without exporting to file")
args = parser.parse_args()


def define_sex_events(es: EventMap):
    # define directed graph of events
    es.add(Sex(EventsSex.FM_HANDJOB_TEASE, "Handjob Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
               With a knowing smirk, you size {THEM} up and put both your hands on their chest.
               Leveraging your weight, you push and trap him against a wall. You slide your knee up his leg 
               and play with his bulge. 
               \\n\\n
               "Is that a dagger in your pocket, or are you glad to see me?"
               \\n\\n
               Tracing your fingers against thin fabric, you work your way up above his trouser before 
               pulling down to free his member. It twitches at the brisk air and the sharp contrast in 
               sensation against your warm hands.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Jerk him off",
                          transition_text="Your continue building a rhythm going up and down his shaft with your hands.",
                          failed_transition_text="You're too turned on to be satisfied with just jerking him off."),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          They start moving a hand to place behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.FM_HANDJOB, "Handjob",
               stam_cost_1=-0.5, stam_cost_2=1,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               desc=f"""
               {THEM}'s eyes are closed and you smirk at your total control of his pleasure.
               You experiment with your strokes, and delight at the immediate feedback on his face.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Continue jerking him off",
                          transition_text=f"""
                          Under the interminable strokes from your hand, {THEM}'s cock has 
                          fully hardened. Dew-like pre dribbles from the tip, lubricating the whole shaft.""",
                          failed_transition_text=
                           ComposedDesc(
                           TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", """
                             You're too turned on to be satisfied with just jerking him off!"""),
                           TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                              {THEM} wants more than your hands, so he #sub takes#! something #italic wetter#!."""), "."
                                        ),
                            ),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""You get on your knees, taking him in your mouth."""),
                   Option(EventsCum.FM_RUINED_ORGASM, OptionCategory.DOM,
                          "Deny his release",
                          transition_text=f"""
                          You abruptly stop your jerking motion and slap his cock, 
                          disrupting the build up to his climax.""",
                          failed_transition_text=f"""
                          You move to stop his climax, but realize that he did not last as long as you expected."""),
                   Option(EventsCum.FM_HANDJOB_CUM_IN_HAND, OptionCategory.DOM,
                          "Milk him into your soft palms",
                          subdom_sub=0,
                          transition_text=f"""
                          You place your open palm below his cock, ready to receive his seed.""",
                          failed_transition_text=f"""
                          You place your open palm below his cock, ready to receive his seed,
                          but his tip seems to be pointing elsewhere...""",
                          ),
                   Option(EventsCum.FM_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make him coat your face in cum",
                          transition_text=f"""
                          You pull away and look up, preparing for him to mark your face.""",
                          ),
               )))
    es.add(Sex(EventsSex.FM_BLOWJOB_DOM, "Dom Blowjob",
               stam_cost_1=0.5, stam_cost_2=2,
               partner_removes_clothes=True,
               animation_left=KNEEL_RULER_3,
               desc=f"""
               You tease his shaft with your tongue, leaving him yearning for your mouth's full commitment.
               In this position of power and control over his pleasure, you deny him any movement with his hands.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Deny him your mouth, replacing it with your hands",
                          weight=5,
                          transition_text=f"""
                          You give {THEM}'s head a last lick, making sure to drag it out as if expressing your tongue's
                          reluctance to part from it. You replace the warmth of your mouth with the milder warmth of
                          your palms, and the bobbing of your head with the strokes from your hands.
                          """,
                          failed_transition_text=f"""
                          The potent musk of his member, inflated by the proximity of your 
                          nose to his groin, strangely captivates you and you lose this opportunity to assert more 
                          dominance."""),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.DOM,
                          "Continue milking his cock with your lips and tongue",
                          transition_text=f"""
                          You continue to bob your head back and forth, occasionally glancing up and making adjustments
                          based on their expression. The fact that you have total control over {THEM}'s pleasure makes
                          you excited.""",
                          failed_transition_text=f"""
                          The incessant invasion of his member down your throat
                          momentarily puts you in a trance, leaving the initiative in his hands.""",
                          subdom_dom_success=0),
                   Option(EventsSex.FM_BLOWJOB_SUB, OptionCategory.SUB,
                          "Let him do the work of thrusting in and out of your mouth",
                          transition_text=f"""
                          Your jaw and neck sore from doing all the work, you decide to let him
                          do pick up the slack. "Come on {THEM}, show me your mettle."
                          \\n\\n
                          Instead of wasting words, he places both hands behind your head and starts thrusting."""),
                   # TODO make these options more likely if you are addicted to cum
                   Option(EventsCum.FM_RUINED_ORGASM, OptionCategory.DOM,
                          "Cruelly deny him his release",
                          transition_text=f"""
                          You pull back and slap his rod, disrupting the build up to his climax.""",
                          failed_transition_text=f"""
                          As you try to pull back, he holds the back of your head with his hands."""),
                   Option(EventsCum.FM_BLOWJOB_CUM_IN_MOUTH_DOM, OptionCategory.SUB,
                          "Milk him dry onto your tongue",
                          transition_text=f"""
                          You prepare to wring him dry with your dexterous tongue."""),
                   Option(EventsCum.FM_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make him coat your face in cum",
                          transition_text=f"""
                          You pull away and look up, preparing for him to mark your face."""),
               )))
    es.add(Sex(EventsSex.FM_BLOWJOB_SUB, "Sub Blowjob",
               stam_cost_1=1.0, stam_cost_2=1.5,
               root_become_more_sub_chance=5,
               partner_removes_clothes=True,
               animation_left=KNEEL_RULER_3,
               desc=f"""
               With your tongue out, your mouth receives {THEM}'s rhythmic thrusts. His hands behind
               your head prevent you from instinctively pulling away, making you feel self conscious about
               being kept captive in a compromising position.""",
               options=(
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.DOM,
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
                   Option(EventsSex.FM_BLOWJOB_SUB, OptionCategory.SUB,
                          "Let him continue his thrusts",
                          transition_text=f"""
                          You adjust your posture better suit his thrusts, making sure to pull away your teeth."""),
                   Option(EventsSex.FM_DEEPTHROAT, OptionCategory.SUB,
                          "Let him thrust even deeper",
                          transition_text=f"""
                          He takes advantage of your lack of strong resistance to dominate your mouth
                          further. Trapping your head with his hands, he plunges deeper while you gag."""),
                   Option(EventsCum.FM_HANDJOB_CUM_IN_HAND, OptionCategory.DOM,
                          "Finish him off on your hand",
                          transition_text=f"""
                          Pulling away, you deprive him of the warmth of your mouth.""",
                          failed_transition_text=f"""
                          Try as you might, {THEM} stops you from pulling away."""),
                   Option(EventsCum.FM_BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.SUB,
                          "Let him cum in your mouth",
                          subdom_sub=0,
                          transition_text=f"""
                          You don't resist when he plunges into your mouth to deposit his seed."""),
                   Option(EventsCum.FM_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make him coat your face in cum",
                          subdom_sub=0,
                          transition_text=f"""
                          You don't resist when he pulls out and aims his rod at your face."""),
               )))
    es.add(Sex(EventsSex.FM_DEEPTHROAT, "Deepthroat",
               stam_cost_1=1.0, stam_cost_2=2.0,
               root_become_more_sub_chance=10,
               partner_removes_clothes=True,
               animation_left=KNEEL_2,
               desc=ComposedDesc("""
               Your eyes tear up as he thrusts deeply and relentlessly. The degrading way in which he
               gives not care about your well-being or pleasure leaves a deep impression on you.""",
                                 TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}", """
               In a dark part of your mind, though you may not admit it, you enjoy being used like
               a cheap toy."""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
               You enjoy being used like a cheap toy, reinforcing your submissive nature."""),
                                 ),
               options=(
                   Option(EventsSex.FM_BLOWJOB_SUB, OptionCategory.DOM,
                          "Take some control back",
                          transition_text=f"""
                          Putting both hands on his waist, you reduce his thrusts to a manageable pace and depth. 
                          """,
                          failed_transition_text=f"""
                          Putting both hands on his waist, you push and try to stop his thrusts.
                          It's all in vain, however, as he ignores you.
                          """),
                   Option(EventsSex.FM_DEEPTHROAT, OptionCategory.SUB,
                          "Continue deepthroating",
                          transition_text=f"""
                          He continues fucking your throat while 
                          your vision blurs against a mixture of tears, saliva, and sex juices."""),
                   Option(EventsCum.FM_BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.SUB,
                          "He cums in your mouth",
                          subdom_sub=0,
                          transition_text=f"""
                          You don't have any say in it, or in anything else at the moment, as his mass
                          fills your throat."""),
               )))
    es.add(Sex(EventsSex.FM_ASS_TEASE, "Ass Tease",
               stam_cost_1=0.5, stam_cost_2=0.75,
               root_become_more_dom_chance=5,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
               Looking into {THEM}'s leering eyes, you can see his desire to have you.
               You may not let them have their way with you, but for now you play along.
               Closing in, you lean close to his ear and promise, "This will be a day you'll remember."
               \\n\\n
               Simultaneously, you reach down and loosen his trousers. His member springs to attention,
               clearly incensed from your womanly wiles and seductive manner. In reciprocation, he pulls
               up your dress, and you turn around, teasingly shake your shapely behind and giving his eyes
               a treat. You continue shaking while backing up until his cock is gripped by your cheeks.
               """,
               options=(
                   Option(EventsSex.FM_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing him with your ass",
                          transition_text=f"""
                          You continue to rub his rod in between your buns. You can feel a sticky coolness
                          from {THEM}'s tip, slicking up your back. The contrast with the rhythmic thrusts from his 
                          hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it."),
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Wrap your fingers around his member and start jerking",
                          transition_text=f"""
                          Feeling a change of pace, you switch to using your hand to get him off.""",
                          failed_transition_text=f"""
                          He recognizes what you are trying to do and twists his body to avoid having his member
                          fully trapped within your fingers."""),
                   Option(EventsSex.FM_HOTDOG, OptionCategory.SUB,
                          "Relax and let him do the thrusting along your crack",
                          transition_text=f"""
                          {THEM} wastes no time after you slow down to pick up the pace, his rod now doing the
                          thrusting along your crack."""),
                   Option(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                          You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                          You try to guide his stream onto your cheeks, but he is cumming too hard to control"""),
                   Option(EventsCum.FM_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over on your groin",
                          subdom_sub=0,
                          transition_text=f"""
                          You feel his dick twitch between your cheeks, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.FM_ASS_RUB, "Ass Rub",
               stam_cost_1=0.5, stam_cost_2=0.75,
               root_become_more_dom_chance=5,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
               Despite not being able to see him standing behind you, 
               you feel a sense of control as you rub his cock and control his pleasure with your ass.
               """,
               options=(
                   Option(EventsSex.FM_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing him with your ass",
                          transition_text=f"""
                          You continue to rub his rod in between your buns. You can feel a sticky coolness
                          from {THEM}'s tip, slicking up your back. The contrast with the rhythmic thrusts from his 
                          hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it"),
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Wrap your fingers around his member and start jerking",
                          transition_text=f"""
                          Feeling a change of pace, you switch to using your hand to get him off.""",
                          failed_transition_text=f"""
                          He recognizes what you are trying to do and twists his body to avoid having his member
                          fully trapped within your fingers."""),
                   Option(EventsSex.FM_HOTDOG, OptionCategory.SUB,
                          "Relax and let him do the thrusting along your crack",
                          transition_text=f"""
                          {THEM} wastes no time after you slow down to pick up the pace, his rod now doing the
                          thrusting along your crack."""),
                   Option(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                          You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                          You try to guide his stream onto your cheeks, but he is cumming too hard to control"""),
                   Option(EventsCum.FM_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                          You feel his dick twitch between your cheeks, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.FM_HOTDOG, "Get Hotdogged",
               stam_cost_1=0.5, stam_cost_2=0.75,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
               You lay back and relax as his cock repeatedly parts your cheeks. He holds your arms
               to keep you from sliding away during his thrusts, which you allow.
               """,
               options=(
                   Option(EventsSex.FM_ASS_RUB, OptionCategory.DOM,
                          "Resume active rubbing to take back some control",
                          transition_text=f"""
                          Having rested a bit by letting him do the thrusting, you restart your own
                          bounce to better control his pleasure.""",
                          failed_transition_text=f"""
                          Having tasted a bit of control, he has no intention of relenting and giving it back to you.
                          """),
                   Option(EventsSex.FM_HOTDOG, OptionCategory.DOM,
                          "Continue to get him off with your ass",
                          dom_success_adjustment=10,
                          transition_text=f"""
                          You enjoy the sensation of controlling his pleasure with just your butt, without having
                          to resort to any penetration.""",
                          failed_transition_text=f"""
                          Your thoughts are occupied by his vigorous thrusts, and you can't help but wonder what it 
                          would feel like to him thrust inside you."""),
                   Option(EventsSex.FM_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Get on top and ride him facing away",
                          dom_success_adjustment=10,
                          transition_text=f"""
                          You push your groin backwards, forcing him to the ground as you get his rod inside you.""",
                          failed_transition_text=f"""
                          You try to force him to the ground, but as you push your groin backwards something
                           #italic enters#! you and {THEM} wraps an arm around your bosom, holding you in place."""),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.DOM,
                          "Switch to using your mouth",
                          dom_success_adjustment=10,
                          transition_text=f"""
                          His vigorous thrusts invade your mind and you can't help but wonder what it would feel like
                          inside of you. You satisfying this curiosity by offering your mouth.""",
                          failed_transition_text=f"""
                          His vigorous thrusts invade your mind and you can't help but wonder what it would feel like
                          inside of you. You won't be satisfied with just him inside your mouth.
                          """),
                   Option(EventsSex.FM_STANDING_FINGERED_FROM_BEHIND, OptionCategory.SUB,
                          "Let him use his fingers",
                          transition_text=f"""
                          As if his earlier thrusting along your ass crack was in preparation, he plunges his fingers
                          into your wet folds, with only a moan as a weak protest from you."""),
                   Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Get impaled from behind",
                          transition_text=f"""
                          One of his thrusts, instead of going up, goes in between your thighs. Your wet folds dribble
                          your anticipation onto his cock. Accepting your body's invitation, his next thrust pierces
                          into you, eliciting a moan from your lips."""),
                   Option(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                          You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                          You try to guide his stream onto your cheeks, but he is climaxing too hard to control"""),
                   Option(EventsCum.FM_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                          You feel his dick twitch between your cheeks, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.FM_STANDING_FINGERED_FROM_BEHIND, "Fingered from Behind",
               stam_cost_1=1, stam_cost_2=-0.5,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               animation_right=SCHADENFREUDE,
               desc=f"""
               His finger #sub squelches against your wet folds#! as he extracts juices from your lower lips while
               extracting moans from your upper lips. Your head leans back and he occasionally takes the liberty
               of entwining his tongue with yours.""",
               options=(
                   Option(EventsSex.FM_HOTDOG, OptionCategory.DOM,
                          "Pull out to recover from his thrusting",
                          transition_text=f"""
                          You pull away from his devious fingers to get a chance to recover.
                          They accept it, for now, and resume thrusting between your buns.""",
                          failed_transition_text=f"""
                          You try to pull away from his devious fingers, but your endeavour is stopped
                          by a particularly deep thrust scraping your inner walls."""),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.DOM,
                          "Satisfy him with your mouth",
                          dom_success_adjustment=5,
                          transition_text=f"""
                          Giving him something else to thrust into, you get on your knees and starting sucking.""",
                          failed_transition_text=f"""
                          You move to pull away from his fingers, but your endeavour is stopped
                          by a particularly deep thrust scraping your inner walls."""),
                   Option(EventsSex.FM_STANDING_FINGERED_FROM_BEHIND, OptionCategory.SUB,
                          "Continue enjoying his deft hands",
                          transition_text=f"""
                          You melt into his hands as you surrender to pleasure."""),
                   Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Let him fuck you proper",
                          transition_text=f"""
                          Surrendering to pleasure and wanting more, you involuntarily push your groin backwards, but find
                           #italic something else#! at your entrance. Welcoming the invitation, he plunges into you fully."""),
                   Option(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                          You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                          You try to guide his stream onto your cheeks, but he is climaxing too hard to control"""),
                   Option(EventsCum.FM_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                          You feel his dick twitch against your ass, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, "Standing Fucked from Behind",
               stam_cost_1=2, stam_cost_2=1.5,
               root_become_more_sub_chance=7,
               root_removes_clothes=True, partner_removes_clothes=True,
               animation_left=BOW_3, animation_right=SCHADENFREUDE,
               desc=ComposedDesc(f"""
               Sometimes bending you over and sometimes #sub pulling your hair to keep you upright#!, 
               you're at the mercy of {THEM}. His vigorous thrusts make you knees weak and you find it
               hard to stay on your feet.
               \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -20", f"""
               "You're my bitch now," he punctuates with a resounding spank on your ass.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "Is that all?" You manage to get out in between his thrusts, taunting and teasing him.
               """),
                                 ),
               options=(
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.DOM,
                          "Pleasure him with your mouth instead",
                          transition_text=f"""
                          You pull away and recover a bit of control by placing your hands and mouth around
                          his cock, where you can easily decide what to do with it.""",
                          failed_transition_text=f"""
                          You attempt to pull away and recover some control, but you find it hard to focus
                          and pull away from this pleasure."""),
                   Option(EventsSex.FM_BLOWJOB_SUB, OptionCategory.DOM,
                          "Let him fuck your mouth instead",
                          dom_success_adjustment=15,
                          transition_text=f"""
                          Dropping to your knees, you replace the hole he thrusts into. {THEM} don't seem to mind and
                          doesn't break their rhythm.""",
                          failed_transition_text=f"""
                          You attempt to extricate yourself with gravity's assistance. However, he grabs your arms
                          and pulls you back, giving you a few sharp thrusts while as punishment for trying to escape."""),
                   Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Submit to getting plowed",
                          transition_text=f"""
                          You accept his invasion, each thrust making it harder and harder to pull away and form
                          coherent thoughts. Instead, your mind is filled with a pink haze, urging you to just accept
                          the pleasure of being used like a piece of meat.
                          """),
                   Option(EventsSex.FM_PRONE_BONE, OptionCategory.SUB,
                          "Submit to getting plowed facing down",
                          transition_text=f"""
                          Your legs weaken as you fall to the floor, {THEM} immediately following you down as he 
                          takes advantage of the opportunity to #sub dominate#! you. You try to prepare yourself for 
                          the #bold intense#! pounding that you're about to recieve.
                          """),
                   Option(EventsCum.FM_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                          "Pull it out, {THEM}!", you just manage to say between his thrusts and groans.""",
                          failed_transition_text=f"""
                          "Pull it out, {THEM}!", you just manage to say between his thrusts and groans, but your pleas falls on deaf ears."""),
                   Option(EventsCum.FM_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let him fill you with his seed",
                          transition_text=f"""
                          Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),
               )))
    es.add(Sex(EventsSex.FM_REVERSE_COWGIRL, "Ride Facing Away",
               stam_cost_1=3, stam_cost_2=1.5,
               root_become_more_dom_chance=15,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
               You close your eyes as your hips hungrily dance around {THEM}'s shaft, #bold shaking#! with pleasure.
               """, TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
               Your senses focus on the hard meat in you, using it with precision to scratch itches no man could ever even #dom hope#! to understand.
               """), TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
               As your senses focus on his hard meat, you can't help but imagine how amazing it would feel to have this rod #sub pounding you!# mercilessly.  
               """),
                                 ),
               options=(
                   Option(EventsSex.FM_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Continue riding him",
                          transition_text=f"""
                          You continue riding {THEM} as he is powerlessly lying under you, his rod constantly hitting the insides of your walls.""",
                          failed_transition_text=f"""
                          You try to continue riding him, but as you slow down a moment he grabs you arms and pushes your waist forward.
                          You nearly topple before feeling a burst of pleasure as {THEM}'s cock enters you.
                          """),
                   Option(EventsSex.FM_COWGIRL, OptionCategory.DOM,
                          "Roll around",
                          transition_text=f"""
                          You turn around, meeting {THEM}'s gaze as you continue riding him.""",
                          failed_transition_text=f"""
                          You try to turn around, but your legs feel weak and {THEM} doesn't miss his opportunity to take the lead and guide your next move.
                          """),
                   Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Stand up and let him take you from behind",
                          transition_text=f"""
                          You stand up, letting him take you however he desires""", ),
                   Option(EventsSex.FM_PRONE_BONE, OptionCategory.SUB,
                          "Lie on your belly and let him pound you",
                          transition_text=f"""
                          You end up on your belly, readying yourself as {THEM} prepares to pound you.""", ),
                   Option(EventsCum.FM_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Make him pull out and cum on your ass",
                          transition_text=f"""
                          You put your hand on his rod, guiding him to unload on your cheeks instead""",
                          failed_transition_text=f"""
                          You put your hand on his rod, trying to guide him to cum on your cheeks instead, but are suddenly grabbed."""),
                   Option(EventsCum.FM_CREAMPIE_ON_TOP, OptionCategory.DOM,
                          "Pin him down and #bold take#! his seed",
                          transition_text=f"""
                          Your body tightens as he begins to twitch inside you.""",
                          failed_transition_text=f"""
                          Your body tightens as he begins to twitch inside you, but you lose control as he grabs your hips and pulls down on them."""),
                   Option(EventsCum.FM_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let #bold him#! fill you with his seed",
                          transition_text=f"""
                          Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),
               )))
    es.add(Sex(EventsSex.FM_COWGIRL, "Ride Facing Them",
               stam_cost_1=2.0, stam_cost_2=1,
               root_become_more_dom_chance=10,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
               You look in {THEM}'s eyes as you vigorously ride, his member under your complete control as you focus exclusively on satisfying yourself. \\n
               """, TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
               He is a tool, his "manhood" nothing more than a meat toy whose #dom only#! purpose is to satisfy your needs. He is a #bold good#! tool.
               """), TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
               Despite how good this feels you can't help but wish #sub he#! was on top of you instead.  
               """),
                                 ),
               options=(
                   Option(EventsSex.FM_COWGIRL, OptionCategory.DOM,
                          "Continue riding him",
                          transition_text=f"""
                          You continue riding {THEM}, his rod madly bouncing from wall to wall inside you as if attempting to escape.""",
                          failed_transition_text=f"""
                          You continue riding him, but as you slow down for a moment {THEM} pushes you backwards, trying to get control over you.
                          """),
                   Option(EventsSex.FM_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Roll around",
                          transition_text=f"""
                          You turn your back towards {THEM}, treating him as no more than a piece of meat.""",
                          failed_transition_text=f"""
                          You begin to turn your back towards him, but your legs feel weak and {THEM} doesn't miss his opportunity to take the lead and guide your next move.
                          """),
                   Option(EventsSex.FM_HOTDOG, OptionCategory.SUB,
                          "Pull out to recover from his thrusting",
                          dom_success_adjustment=10,
                          transition_text=f"""
                          {THEM} twitches backwards, managing to get up, as he escapes from under you.""", ),
                   Option(EventsSex.FM_MISSIONARY, OptionCategory.SUB,
                          "Lie on your back and let him pound you",
                          transition_text=f"""
                          You end up on your back, readying yourself as {THEM} lifts your legs, making way for his rod.""", ),
                   Option(EventsCum.FM_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Make him pull out and cum on your ass",
                          transition_text=f"""
                          You put your hand on his rod, guiding him to unload on your cheeks instead""",
                          failed_transition_text=f"""
                          You put your hand on his rod, trying to guide him to cum on your cheeks instead, but are suddenly grabbed."""),
                   Option(EventsCum.FM_CREAMPIE_ON_TOP, OptionCategory.DOM,
                          "Pin him down and #bold take#! his seed",
                          transition_text=f"""
                          Your body tightens as he begins to twitch inside you.""",
                          failed_transition_text=f"""
                          Your body tightens as he begins to twitch inside you, but you lose control as he grabs your hips and pulls down on them."""),
                   Option(EventsCum.FM_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let #bold him#! fill you with his seed",
                          transition_text=f"""
                          Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),

               )))
    es.add(Sex(EventsSex.FM_MISSIONARY, "Lie on Back",
               stam_cost_1=2.0, stam_cost_2=1.5,
               root_become_more_sub_chance=10,
               animation_left=FLIRTATION_LEFT, animation_right=FLIRTATION_LEFT,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
               You lie there, legs straddling his shoulders, each of {THEM}'s vigorous thrusts slapping loudly against your cheeks as
               waves of pleasure course through your core. You have nearly no control over your body
               """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                and you wish you had even #sub less#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                and you #dom hate#! that it feels this good"""), "."
                                 ),
               options=(
                   Option(EventsSex.FM_COWGIRL, OptionCategory.DOM,
                          "Roll with him and get on top",
                          transition_text=f"""
                          You grab {THEM} as he's recovering from a thrust and push him sideways with all your strength, landing on top of him.""",
                          failed_transition_text=f"""
                          You grab {THEM} as he's recovering from a thrust and manage to get on your side, but he grabs and puts you back down.
                          """),
                   Option(EventsSex.FM_MISSIONARY, OptionCategory.SUB,
                          "Keep your legs up",
                          transition_text=f"""
                          You keep your legs up, letting {THEM} continue nailing you from above."""),
                   Option(EventsSex.FM_PRONE_BONE, OptionCategory.SUB,
                          "Roll in place, submitting completely",
                          transition_text=f"""
                          You find yourself rolled onto your belly, your opening at {THEM}'s mercy."""),
                   Option(EventsCum.FM_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                          "Not inside!" you barely blurt out between moans and labored breaths.""",
                          failed_transition_text=f"""
                          "Not inside!" you barely blurt out between moans and labored breaths, but your pleas falls on deaf ears."""),
                   Option(EventsCum.FM_CREAMPIE_KEEP, OptionCategory.DOM,
                          "Hold him inside while he's cumming",
                          transition_text=f"""
                          You wrap your legs and arms around him...""",
                          failed_transition_text=f"""
                          You try to wrap your legs and arms around him, but his wild thrusting makes it impossible to hold on."""),
                   Option(EventsCum.FM_CREAMPIE_BRED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                          His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))
    es.add(Sex(EventsSex.FM_PRONE_BONE, "Lie Face Down",
               stam_cost_1=3.5, stam_cost_2=2.5,
               root_become_more_sub_chance=15,
               animation_left=FLIRTATION_LEFT, animation_right=FLIRTATION_LEFT,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
               You are face down with your legs closed while {THEM} thrusts deep in your moist womb, your mind melting from the echoing sound of
               #bold your cheeks getting clapped#! as each #italic ravaging#! stroke sends #sub paralyzing#! jolts of pleasure through your whole being. \\n\\n
               He's in complete control of your body and mind
               """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                and you're enjoying #sub every#! single moment of him #italic splitting you in half#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                and you #dom hate#! having to admit to yourself that he might #italic break#! you"""), "."
                                 ),
               options=(
                   Option(EventsSex.FM_MISSIONARY, OptionCategory.DOM,
                          "Roll in place",
                          transition_text=f"""
                          You find an opening between {THEM}'s thrusts and manage to roll in place, your body now facing his,
                           but he quickly spreads your legs out of the way of his prick.""",
                          failed_transition_text=f"""
                          You try to roll in place, but {THEM}'s #bold paralyzing#! barrage of thrusts never slows enough to do so.
                          """),
                    Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.DOM,
                          "Get up",
                          transition_text=f"""
                          You find a moment between thrust and pull your knees under you, managing to get up, but {THEM}'s relentless assault
                          continues as he holds your arms while entering you once more.""",
                          failed_transition_text=f"""
                          You try to find a moment to pull your knees under you, but each attempt is thwarted by his wild thrashing."""),
                   Option(EventsSex.FM_PRONE_BONE, OptionCategory.SUB,
                          "Submit to getting #bold mercilessly#! plowed",
                          transition_text=f"""
                          The immense warmth of {THEM} pounding you to the core makes your body melt as your mind is #sub flooded with heat#!.
                          """,
                          ),
                   Option(EventsCum.FM_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                          "D-Don't fill me!" you shakingly say as his pounding nearly drives you senseless.""",
                          failed_transition_text=f"""
                          "D-Don't fill me!" you shakingly say as his pounding nearly drives you senseless, but your pleas falls on deaf ears."""),
                   Option(EventsCum.FM_CREAMPIE_BRED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                          His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))


class Modifier:
    def __init__(self, modifier: str, duration: typing.Optional[str] = None, root=True):
        self.modifier = modifier
        self.duration = duration
        self.root = root


class AddModifier(Effect):
    def __init__(self, *args: Modifier):
        self.modifiers = args

    def __call__(self, b: BlockRoot):
        for mod in self.modifiers:
            if mod.root:
                self.assign_single_mod(b, mod)
            else:
                with Block(b, AFFAIRS_PARTNER):
                    self.assign_single_mod(b, mod)

    @staticmethod
    def assign_single_mod(b: BlockRoot, mod: Modifier):
        with Block(b, ADD_CHARACTER_MODIFIER):
            b.assign(MODIFIER, mod.modifier)
            if mod.duration:
                b.add_line(mod.duration)


# TODO add chance of acquiring fetishes
def define_cum_events(es: EventMap):
    es.add(Cum(EventsCum.FM_HANDJOB_CUM_IN_HAND, "A Cumshot in Hand is Worth Two in the Bush",
               subdom_change=1, root_become_more_dom_chance=20,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean your hands on a nearby cloth"),
               animation_left=BOREDOM, animation_right=SHAME,
               desc=ComposedDesc("""
               His back arches, instinctively thrusting forward to fill an imaginary womb as he spurts his load onto your open palm.
               \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", """
               "That's it?" you say as you wipe his seed onto his chest, "How do you hope to please any
               woman with that pathetic stamina?" His #dom dejected look 
               pleases#! you #italic - maybe your personality is twisted?#!
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               "Not bad, {THEM}!", you say while taking note of his #!italic potential#! for any possible future encounters.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", """
               "Impressive!", you say as you suck one of your fingers clean, "Maybe use that #sub intensity#! for
                #!italic something else#! next time?"
               """),
                                 )))
    es.add(Cum(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, "Icing on the Cake",
               subdom_change=0,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean yourself and get dressed"),
               desc=ComposedDesc(f"""
               You don't see it as much as feel it when a few splashes of warmth land on your ass, signaling the end of
               this session. Some starts tracing a warm path down your legs while the rest stay,
               a compliment to your curves. #italic Is it normal for your thoughts to wander so quickly
               after sex?#!""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                #italic Yes, it is - their #dom petty#! desires don't deserve your atention.#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                #italic Maybe they wouldn't if he'd taken some #sub initiative#! instead of being satisfied with this.#!"""),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               \\n\\n"Thank you for letting me grind against your buns, {ME_FULL_REGNAL}", {THEM} says while devotedly cleaning you up.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               \\n\\n"This was fun", {THEM} says enthusiastically while #italic clearly#! staring at your shapes yearningly.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               \\n\\n"Let's do more next time", {THEM} says as you feel a sudden #sub smack on your ass#!. 
               """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                \\n\\nYou #dom chuckle#! at his reaction, asking yourself if you're ever going to face a #S real#! challenge in the sheets ."""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                \\n\\nYou wish his reaction would have been more... #sub intense#!, to say the least."""),
                                 ),
               ))
    es.add(Cum(EventsCum.FM_BLOWJOB_CUM_ON_FACE, "Painting your Face",
               subdom_change=-2, root_become_more_sub_chance=15,
               animation_left=SHAME, animation_right=SCHEME,
               terminal_option=Option(None, OptionCategory.OTHER, "Sample some stray globs of cum"),
               desc=ComposedDesc(f"""
               You look up and brace yourself for what's to come. When the first drop hits your face,
               you flinch and instinctively close your eyes, which was fortunate as you feel a glob
               land on your eyelids.
               \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "Impudent knave!" You object while wiping away those near your eyes. "At least have the decency
               to aim away from my eyes!" He better #dom behave#! if he wishes to see you again.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               As you open your eyes you are met with {THEM}'s pleased expression. "You look great", he remarks with a smile.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               "You look beautiful covered in my cum," {THEM} say while #sub wiping his cock against your face#!.
               Taking advantage of your helpless state, he takes some liberties in degrading you,
               \\n\\n
               "Regardless of who you lay with later, even with them, you'll remember this moment with my cum marking your face."
               """),
                                 
                                 )))
    es.add(Cum(EventsCum.FM_BLOWJOB_CUM_IN_MOUTH_DOM, "Satisfying your Sweet Tooth",
               subdom_change=-1, root_become_more_sub_chance=10,
               animation_left=DISGUST, animation_right=SCHADENFREUDE,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe away any cum that might've escaped"),
               # TODO triggered text depending on cum fetish
               desc=f"""
               {THEM} arches his back and holds your head in place with his hands.
               You move to free your head, but with his release imminent, he has no intention to listen to orders.
               Soon, you feel {THEM}'s cock twitch in your mouth followed by a salty deluge.
               
               His #sub seed is thick#!, and combined with its salty taste makes it quite conventionally unpalatable.
               """
               ))
    es.add(Cum(EventsCum.FM_BLOWJOB_CUM_IN_MOUTH_SUB, "Down the Gullet",
               subdom_change=-2, root_become_more_sub_chance=20,
               animation_left=SHAME, animation_right=SCHADENFREUDE,
               terminal_option=Option(None, OptionCategory.OTHER, "Recover from having your throat used so roughly"),
               desc=ComposedDesc(f"""
               {THEM} holds your head in place while his last thrust goes deeper than before.
               His dick twitches and shoots out his seed in a steady stream which fills up your mouth
               as he makes no move to remove his member. 
               \\n\\n""",
               TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "Swallow it," he says in a commanding tone.
               """),
               """
               \\n\\n
               As you have no choice apart from drowning, you swallow it. Fortunately or not, since he
               thrusted so deeply, most of it was shot into the back of your throat where you cannot taste it.
               You #sub gulp audibly and take it all down#!.
               \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               "You look beautiful covered in my cum," {THEM} says while #sub wiping his cock against your face#!.
               Taking advantage of your helpless state, he takes some liberties in degrading you.
               \\n\\n
               """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
               Regardless of who you lay with later, you'll remember this moment with his cum marking your face.
               """, ),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
               Seems like {THEM} needs to be #dom put#! in his place, bold ruffian that he is. 
               """, ),           
                                 )
               ))
    es.add(Cum(EventsCum.FM_RUINED_ORGASM, "A Firm Grasp on His Release",
               subdom_change=2, root_become_more_dom_chance=35,
               animation_left=DISMISSAL, animation_right=BEG,
               terminal_option=Option(None, OptionCategory.OTHER, "Leave him yearning and frustrated"),
               desc=f"""
               {THEM} arches his back he's clearly about to to climax, but you interrupt by firmly grabbing his
               shaft close to his body. Even if he wanted to, he physically cannot release his seed.
               "Did I say you could cum?" You cruelly intone as you grasp his balls with your other hand.
               \\n\\n
               "Please, I'm so close," he whines.
               \\n\\n
               "You didn't earn it today," you respond, "maybe next time #dom if you please me.#!"
               """,
               custom_immediate_effect=AddModifier(Modifier(SEXUALLY_FRUSTRATED, duration=f"{YEARS} = 1", root=False))
               ))
    es.add(Cum(EventsCum.FM_PULL_OUT_CUM_ON_ASS, "More Icing on the Cake",
               subdom_change=-1,
               preg_chance_1=0.05 * PREGNANCY_CHANCE,
               animation_left=FLIRTATION_LEFT, animation_right=PERSONALITY_BOLD,
               root_become_more_sub_chance=10,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean yourself and get dressed"),
               desc=ComposedDesc(
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               Fearing the consequences of impregnating you, {THEM} pulls out just before he goes past his limit.
               He instead shoots his seed on your ass, several spurts of warmth announcing the end of the session. \\n\\n
               "It is a privilege to satisfy your womb's needs, {ME_FULL_REGNAL}", he says while devotedly cleaning you up.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               Perhaps fearing the consequences of impregnating you or just showing some courtesy, {THEM} pulls out just as he reaches his limit.
               He instead shoots his seed on your ass and holes, several spurts of warmth announcing the end of the session.
                \\n\\n
               "What happens next?", he says while #italic clearly#! staring at your shapes with a lustful gaze.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               Perhaps out of courtesy or simply not wanting to impregnate you, {THEM} pulls out just as he goes past his limit.
               He instead shoots his seed on your whole groin, several spurts of warmth announcing the end of the session. \\n\\n
               With a sudden #sub smack on your ass#!, "Let's meet again soon."
               """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                \\n\\n"Come again sometime, will you? I'd like it if you did #sub more#! to me", you say with a smile """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                \\n\\n"Good boy", you whisper in {THEM}'s ear while #dom patting#! him on the head.
                "I #S might#! just invite you over again if I ever need something", you say with a smirk.""")
               ),
               ))
    es.add(Cum(EventsCum.FM_CUM_ON_GROIN, "Coated in White",
               subdom_change=-1,
               root_become_more_sub_chance=5,
               preg_chance_1=PREGNANCY_CHANCE * 0.01,
               animation_left=DISMISSAL, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean up the white coating on your groin"),
               desc=ComposedDesc(f"""
               {THEM} stops himself mere inches from your groin, coating your hips and holes with a thick layer of white. 
               \\n\\n
               Your can feel his warmth #sub on#! you.""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                #italic Yes, it is - their #dom petty#! desires don't deserve your atention.#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                #italic Maybe they wouldn't if he'd taken some #sub initiative#! instead of being satisfied with this.#!"""),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               \\n\\n"Pardon me, {ME_FULL_REGNAL}!", {THEM} says while devotedly cleaning you up.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               \\n\\n"This was fun", {THEM} says as he runs his hand across your shapes before dressing.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               \\n\\n"Let's do more next time", {THEM} says as you feel a sudden #sub smack on your ass#!. 
               """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                Ugh, that fool made #dom such#! a mess!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                If only he'd done #sub more#! to you!"""), 
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_REGULAR, "Plowing the Fields",
               subdom_change=-3,
               root_become_more_sub_chance=20,
               preg_chance_1=PREGNANCY_CHANCE,
               animation_left=WORRY, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe away the cum dripping down your thighs"),
               desc=ComposedDesc(f"""
               "Ugh," {THEM} grunts as he plunges to the hilt, his rod violently throbbing inside you.
                A white contour gathers on your lips as his load flows out.""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", """
               "I-I don't know what came over me!" he says, avoiding your gaze with a look of deep shame across his face.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               "You were just so tight!", {THEM} awkwardly says, as if trying to justify himself.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", """
               With a #sub smack on your ass#!, "Let's do this again sometime.", before finally pulling out.
               """),
                                 """\\n\\nYou're left standing as his seed #sub seeps#! out of your slit, your body enjoying the newfound warmth within it. \\n\\n""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
               Your body brimming with anticipation as you softly say: "Y-you can do it again if you want". You #bold #sub want#!#! him to do it again, \\n"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
               Is the #dom privilege#! of experiencing your body not enough?! How #dom dare#! he release inside you whenever he wishes
                like in some #italic random peasant maid?!#!"""),
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_ON_TOP, "Cherry on Top",
               subdom_change=3,
               root_become_more_dom_chance=30,
               preg_chance_1=PREGNANCY_CHANCE,
               animation_left=FLIRTATION_LEFT, animation_right=SHOCK,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe the silky threads hanging from your slit"),
               desc=ComposedDesc(f"""
               {THEM} grunts when your slit fully swallows his rod, his muscles locking up as surges of soft warmth coat your insides.
               \\n\\n 
               """,
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} < -10", f"""
               "When did you get so #dom rough #!?!", he says with a #italic shocked #! expression on his face while still pinned below you,
                his attempts at wriggling out only pleasing you further.\\n\\n
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               "I didn't mean to, but it just felt so good!", {THEM} says as he pulls out, his gaze lingering on your #bold stuffed#! hole.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > 10", f"""
               "Whatever you need, my {ME_LADY_LORD}!", he says while #dom submitting# to being milked in your womb\\n\\n
               """),
                                 """You slowly get up, white threads hanging from your slit as drops splash onto the ground. """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
               You stare intently into his eyes, knowing he couldn't have stopped you from #dom taking#! his seed no matter how hard he tried - so #dom you did#!.""")
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_BRED, "Something to Remember Him By",
               subdom_change=-3,
               root_become_more_sub_chance=45,
               preg_chance_1=PREGNANCY_CHANCE * 1.5,
               animation_left=WORRY, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER,
                                      "Feel his seed trickle from your slit for the rest of the day"),
               desc=ComposedDesc(
                   f"""
                {THEM} grunts loudly with a look of ecstasy on his face as he unloads in you, pushing further in with each deep thrust
                 - you feel a growing #bold warmth#! begin coating your insides...
               \\n\\n
                """,
                   """You lie there panting, a white sliver dripping from your #sub conquered#! slit as his seed #bold fills#! your womb.""",
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
               He plowed you like a cheap whore, his pounding climaxing as he filled you up and you had with #sub no say#! in it.
                Are you so irresistible that he couldn't help but cum inside """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB} \n {NOT} = {{ {HAS_TRAIT} ={PREGNANT} }}", f"""
               or is he #italic trying#! to breed you? Either way, you #sub love#! the feeling.""", ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB} \n {HAS_TRAIT} = {PREGNANT}", f"""
               even with a bun already in you? How #sub flattering#!.""", ),
                   """\\n\\n""",

                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "M-my {ME_LADY_LORD}!", {THEM} blurts out while staring at your stuffed hole in shock.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 20", f"""
               "I'll clean it, forgive me!", he pleads as he starts #dom licking#! you clean, having pulled out #S far#! too late.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10 \n{HAS_TRAIT} = {LIDA_DOM}", f"""
               \\n"Leave, #dom fool#! you say #warning furiously#! while kicking him away from your slit, banishing him bare from the chamber.
               """),

                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               "You're #sub mine#! now, {ME_NAME}", {THEM} whispers in your ear before finally beginning to pull out.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -20", f"""
               You moan sharply as he thrusts in to the hilt one last time, your back #italic arching#! from the sudden
                jolt of pleasure as your mind #sub gives in#! to the #S heat#! stirring up inside your belly.
               """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10 \n{HAS_TRAIT} = {LIDA_SUB}", f"""
               \\n\\n"Come again sometime", you say with a #italic #sub smile#!#!. He #sub smacks#! your ass with a grin,
                running two fingers along your slit before starting to dress.  
               """),

                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
               \\n\\nAs if getting fucked like a cheap whore wasn't enough, he even #warning seeded#! you like you're just some servant girl at a feast! 
               """, ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM} \n {NOT} = {{ {HAS_TRAIT} ={PREGNANT} }}", f"""
               To enjoy the warmth of your womb is an #italic unrivaled privilege#!,
                how #S #dom dare#!#! he demand more by trying to #S mate with you!?#!
               """, ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM} \n {HAS_TRAIT} = {PREGNANT}", f"""
               Were you not already with child, {THEM} might've #S bred#! you - and you #S #dom deeply loathe#!#! the thought.
               """, ),

                   TriggeredDesc(
                       f"{NOT} = {{ {HAS_TRAIT} ={PREGNANT} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_DOM} }}",
                       f"""
               \\n\\nThis isn't quite how you were expecting your dalliance to end...
               """, ),
                   TriggeredDesc(
                       f"{HAS_TRAIT} ={PREGNANT} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_DOM} }}",
                       f"""
               \\n\\nAt least the #italic indiscreet#! ending of this dalliance won't have any #S unwanted#! consequences.
               """, ),
               ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_KEEP, "Taking It Home",
               subdom_change=1,
               root_become_more_dom_chance=20,
               preg_chance_1=PREGNANCY_CHANCE * 2,
               animation_left=ECSTASY, animation_right=SHOCK,
               terminal_option=Option(None, OptionCategory.OTHER, "No need to clean up, it's #bold all#! inside you"),
               desc=ComposedDesc(f"""
               As you feel {THEM} close to finishing you clasp around him, each tense twitch of his rod keeping him #dom locked#!
                inside as he #S fully#! unloads his hot load in your womb.
               \\n\\n
                """,
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "Whatever you need, {ME_FULL_REGNAL}!", he says submissively, yet #italic clearly satisfied#! as you finally release him.\\n\\n
               """, ),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} < 10", f"""
               "{ME_NAME}, what are you doing?!", he exclaims, clearly #italic surprised#! before finally managing to pull out. \\n\\n
               """, ),
                                 f"""You lie on your back, knees to your chest, full and satisfied that you've #dom taken#! what you wanted.\\n""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
               You're not usually this assertive, but you #bold #dom yearned#!#! to keep his warmth #sub inside you.#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
               Did he think you'd let him have his way with your body just for fun? #dom Fool.#!""")
                                 )
               ))


def define_first_events(es: EventMap):
    source_sex_events = get_source_sex_events(es)
    es.add(First(EventsFirst.MEETING_WITH_SPOUSE, "Spicing it Up",
                 source_sex_events=source_sex_events, background="bedchamber",
                 desc=f"""
                 You light some candles and sprinkle some scented petals in your bedchamber,
                 making it an even more inviting den of intimacy. As before, you left
                 a cryptic message inviting {THEM}.
                 \\n\\n
                 He arrives promptly, clearly excited with your spontaneous trysts, and only
                 gives a brief greeting before climbing into bed with you."""))
    es.add(First(EventsFirst.MEETING_WITH_SPOUSE_INITIAL, "Flowers in Bloom",
                 source_sex_events=source_sex_events, background="garden",
                 desc=f"""
                 As it is beautiful day, you have a stroll in your garden. 
                 In your bed chambers, you left a note to invite {THEM} outside.
                 \\n\\n
                 Upon spotting you, he rushes forward, "What is it you wanted to see me
                 about?" Curious, and a little bit panicked with the cryptic content of your message.
                 \\n\\n
                 Instead of answering, you beam him your brightest smile, 
                 "Let's make love here," pointing to a shaded awning free from prying eyes.
                 \\n\\n
                 Your strategy to put him on his toes and then deliver such a direct line works
                 and he stands there, flustered at your proposal but not rejecting it.
                 """))
    es.add(First(EventsFirst.MEETING_WITH_VASSAL, "Chains of Command",
                 source_sex_events=source_sex_events, background="study",
                 desc=f"""
                 You send a summons to {THEM} about helping you with interpreting some passages in your study.
                 By now, that's tacitly understood as an invitation to a tryst, which he gladly accepts.
                 Almost immediately, he shows up in your study.
                 """))
    es.add(First(EventsFirst.MEETING_WITH_VASSAL_INITIAL, "Privileges of Power",
                 source_sex_events=source_sex_events, background="study",
                 desc=f"""
                 You summon {THEM} to your study, giving instructions to your 
                 guards to let him in then leave afterwards. The guards' faces betray their guesses,
                 but you pay them to be discrete thus they make no comments.
                 \\n\\n
                 Entering the study, "You summoned me, my Lady?"
                 \\n\\n
                 "Yes, I want to consult with you on this passage here", you say as you reach for one of the books
                 on your bookshelf, making sure that as you do so, one of the straps on your dress would come loose
                 and present your feminine assets. Blushing, they turn away, but you pretend as if you didn't notice 
                 and instead walk up to him and say in a coy tone, "Could you help me with this?"
                 """))
    es.add(First(EventsFirst.MEETING_WITH_LIEGE, "Mead in my Room?",
                 source_sex_events=source_sex_events, background="bedchamber",
                 desc=f"""
                 It's another long council meeting, and {THEM}'s councillors start streaming out of the
                 room. You, however, remain in the room and say, "My Lord, I have some more council
                 business to discuss with you."
                 \\n\\n
                 Nodding, he responds, "Very good, I appreciate your enthusiasm and hard work."
                 Taking a pause, "But it's getting late, so let us retire to my bedchambers where
                 we can discuss it in more comfort."
                 """))
    es.add(First(EventsFirst.MEETING_WITH_LIEGE_INITIAL, "An Intimate Discussion",
                 source_sex_events=source_sex_events, background="council_chamber",
                 animation_left=BOW,
                 desc=f"""
                 After the council meeting, {THEM} dismisses you all. However, you take your time
                 leaving and soon you two are the only ones left in the chamber. "Is there something
                 you need?" he asks amicably.
                 \\n\\n
                 Instead of answering, you twirl your hair and put an arm under your bosom, making
                 an effort to highlight it. You saunter closer to him and see an inviting amusement in 
                 his eyes, "You, my Lord."
                 """))
    es.add(First(EventsFirst.MEETING_WITH_PRISONER, "Taste of Heaven in Hell",
                 source_sex_events=source_sex_events, background="dungeon",
                 animation_right=PRISON_HOUSE,
                 desc=f"""
                 You descend to {THEM}'s cell without much ceremony.
                 \\n\\n
                 "You've come again," he says happily. Laughing, he jests#weak (?)#! "Have you fallen
                 for my cock?"
                 \\n\\n
                 That comment strikes a cord within you and you question your repeated visit to your prisoner.
                 Initially it was meant as a torture for them, but that is only valid if you deny him the pleasure
                 afterwards. #sub;italic Perhaps you are growing dependent on the pleasure he can provide?#!
                 \\n\\n
                 Pushing such thoughts to the back of your mind, you approach him."""))
    es.add(First(EventsFirst.MEETING_WITH_PRISONER_INITIAL, "The Sweetest Torture",
                 source_sex_events=source_sex_events, background="dungeon",
                 animation_right=PRISON_HOUSE,
                 desc=f"""
                 You descend down the stone stairs to your dungeon and muse that giving a prisoner
                 pleasure might be the greatest torture after you take it away. After all, ignore is bliss,
                 and to take away that bliss would be fitting punishment.
                 \\n\\n
                 It doesn't take you long before you arrive in front of {THEM}'s cell. Speaking to the guards,
                 "I need to talk to this prisoner along; you are dismissed."
                 \\n\\n
                 He looks up, eyes wide in fear of what tortures you have devised that requires a personal visit.
                 But you also notice a bulge forming in his loose trousers. Before coming, you had your makeup and
                 perfume done in a manner bordering on garish (and some would call #sub whorish#!), the kind that
                 instantly sparks men's loins and their desire to dominate and conquer.
                 """))
    es.add(First(EventsFirst.MEETING_WITH_ACQUAINTANCE, "Who Owns Who",
                 source_sex_events=source_sex_events, background="sitting_room",
                 desc=f"""
                 Communicating via your servants, you inform {THEM} that you'd like to get to know them better
                 in your sitting room. Wise to your intentions, he wastes no time arriving, noting the lack of 
                 servants and guards to confirm his guess.
                 \\n\\n
                 You lock eyes, and without exchanging any words do all the communication with your bodies."""))
    es.add(First(EventsFirst.MEETING_WITH_ACQUAINTANCE_INITIAL, "A Chance Encounter",
                 source_sex_events=source_sex_events, background="courtyard",
                 desc=f"""
                 Your servants inform you that {THEM} is strolling along your courtyard. You give further instructions
                 to clear out the guards and any other personage near that location. A knowing gleam appears in their
                 eyes, but they are paid for their discretion and so bow and leave without any comment.
                 \\n\\n
                 You find him in the expected location, and feigning like you were strolling as well, you don't
                 go towards him.
                 \\n\\n
                 "Well met, {ME_FULL_REGNAL}!" He greets you enthusiastically.
                 \\n\\n
                 Smiling, you reply, "{THEM}, no need to stand on formality. Fate has ordained that we
                 meet today, it must mean that we should get to know each other more intimately."
                 Your painted lips and inviting body language draws them in with no chance of escape."""))


if __name__ == "__main__":
    es = EventMap()
    define_sex_events(es)
    define_cum_events(es)
    # find/specify all source sex events, which are ones which have at most themselves as input events
    link_events_and_options(es)
    # can only define this after linking options since we need incoming options
    define_first_events(es)
    all_options = link_events_and_options(es)

    # warn about any undefined events
    for eid in list(EventsFirst) + list(EventsSex) + list(EventsCum):
        if eid not in es.events:
            print(f"WARNING: {eid} declared but not defined")

    # plot directed graph of events and options (graphviz)
    export_dot_graphviz(es)
    export_strings(*generate_strings(es, all_options), dry_run=args.dry)
