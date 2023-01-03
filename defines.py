import enum
import typing

UTF8_BOM = u'\ufeff'
debug = True
# indirectly also max number of options we can have * 100
option_from_to_offset = 1000000
base_event_weight = 5
max_options_per_type = 2


class EventsFirst(enum.Enum):
    # FM
    FM_MEETING_WITH_SPOUSE = 1
    FM_MEETING_WITH_SPOUSE_INITIAL = 2
    FM_MEETING_WITH_VASSAL = 3
    FM_MEETING_WITH_VASSAL_INITIAL = 4
    FM_MEETING_WITH_LIEGE = 5
    FM_MEETING_WITH_LIEGE_INITIAL = 6
    FM_MEETING_WITH_PRISONER = 7
    FM_MEETING_WITH_PRISONER_INITIAL = 8
    FM_MEETING_WITH_ACQUAINTANCE = 9
    FM_MEETING_WITH_ACQUAINTANCE_INITIAL = 10
    # MF
    MF_MEETING_WITH_SPOUSE = 11
    MF_MEETING_WITH_SPOUSE_INITIAL = 12
    MF_MEETING_WITH_VASSAL = 13
    MF_MEETING_WITH_VASSAL_INITIAL = 14
    MF_MEETING_WITH_LIEGE = 15
    MF_MEETING_WITH_LIEGE_INITIAL = 16
    MF_MEETING_WITH_PRISONER = 17
    MF_MEETING_WITH_PRISONER_INITIAL = 18
    MF_MEETING_WITH_ACQUAINTANCE = 19
    MF_MEETING_WITH_ACQUAINTANCE_INITIAL = 20


class EventsSex(enum.Enum):
    FM_WHIP_TEASE = 1
    FM_FOOTJOB_TEASE = 2
    FM_HANDJOB_TEASE = 3
    FM_ASS_TEASE = 4
    FM_PUSSY_TEASE = 5
    FM_TIT_TEASE = 6
    FM_HANDJOB = 7
    FM_BLOWJOB_DOM = 8
    FM_STANDING_FUCKED_FROM_BEHIND = 9
    FM_BLOWJOB_SUB = 10
    FM_DEEPTHROAT = 11
    FM_HOTDOG = 12
    FM_STANDING_FINGERED_FROM_BEHIND = 13
    FM_ASS_RUB = 14
    FM_REVERSE_COWGIRL = 15
    FM_COWGIRL = 16
    FM_MISSIONARY = 17
    FM_PRONE_BONE = 18
    MF_WHIP_TEASE = 19
    MF_FOOTJOB_TEASE = 20
    MF_HANDJOB_TEASE = 21
    MF_ASS_TEASE = 22
    MF_DICK_TEASE = 23
    MF_HANDJOB = 24
    MF_BLOWJOB_DOM = 25
    MF_STANDING_FUCKED_FROM_BEHIND = 26
    MF_BLOWJOB_SUB = 27
    MF_DEEPTHROAT = 28
    MF_HOTDOG = 29
    MF_STANDING_FINGERED_FROM_BEHIND = 30
    MF_ASS_RUB = 31
    MF_REVERSE_COWGIRL = 32
    MF_COWGIRL = 33
    MF_MISSIONARY = 34
    MF_PRONE_BONE = 35
    FM_FOOTJOB = 36
    FM_BLOWJOB_DOM_I = 37
    FM_BLOWJOB_DOM_II = 38


class EventsCum(enum.Enum):
    FM_HANDJOB_CUM_IN_HAND = 1
    FM_BLOWJOB_CUM_IN_MOUTH_DOM = 2
    FM_BLOWJOB_CUM_IN_MOUTH_SUB = 3
    FM_BLOWJOB_CUM_ON_FACE = 4
    FM_RUINED_ORGASM = 5
    FM_ASS_TEASE_CUM_ON_ASS = 6
    FM_CUM_ON_GROIN = 7
    FM_PULL_OUT_CUM_ON_ASS = 8
    FM_CREAMPIE_REGULAR = 9
    FM_CREAMPIE_ON_TOP = 10
    FM_CREAMPIE_BREED = 11
    FM_CREAMPIE_KEEP = 12

    MF_HANDJOB_CUM_IN_HAND = 13
    MF_BLOWJOB_CUM_IN_MOUTH_DOM = 14
    MF_BLOWJOB_CUM_IN_MOUTH_SUB = 15
    MF_BLOWJOB_CUM_ON_FACE = 16
    MF_RUINED_ORGASM = 17
    MF_ASS_TEASE_CUM_ON_ASS = 18
    MF_CUM_ON_GROIN = 19
    MF_PULL_OUT_CUM_ON_ASS = 20
    MF_CREAMPIE_REGULAR = 21
    MF_CREAMPIE_ON_TOP = 22
    MF_CREAMPIE_BREED = 23


# alias for any event type
EventId = typing.Union[EventsFirst, EventsSex, EventsCum]


def yes_no(boolean: bool):
    return YES if boolean else NO


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
RANDOM_VALID = "random_valid"
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
# depending on the type of event, either the root or partner's stamina decides how events are finished
FINISHER_STAMINA = "finisher_stamina"

DOM_CHANCE = "dom_chance"
DOM_SUCCESS = "dom_success"
THIS_DOM_CHANCE = "this_dom_chance"
DOM_SUCCESS_ADJUSTMENT = "dom_success_adjustment"
DOM_ATTEMPT_TOOLTIP = "attempt_dom_tooltip"
DOM_NO_SUB_TOOLTIP = "dom_no_sub_tooltip"
VOLUNTARY_SUB_TOOLTIP = "voluntary_sub_tooltip"
DOM_SUCCESS_ADJUSTMENT_TOOLTIP = "dom_success_adjustment_tooltip"
DOM_CHANCE_SUBDOM_NATURE_TOOLTIP = "dom_chance_subdom_nature_tooltip"
DOM_CHANCE_SUBDOM_TOOLTIP = "dom_chance_subdom_tooltip"
DOM_CHANCE_PROWESS_TOOLTIP = "dom_chance_prowess_tooltip"
DOM_CHANCE_LUST_BEAUTY_TOOLTIP = "dom_chance_lust_beauty_tooltip"
DOM_CHANCE_TITLE_AUTHORITY_TOOLTIP = "dom_chance_title_authority_tooltip"
DOM_CHANCE_STUBBORNESS_TOOLTIP = "dom_chance_stubborness_tooltip"
DOM_CHANCE_STAMINA_TOOLTIP = "dom_chance_stamina_tooltip"
DOM_CHANCE_ORGASM_TOOLTIP = "dom_chance_orgasm_tooltip"
DOM_CHANCE_SEX_SKILL_TOOLTIP = "dom_chance_sex_skill_tooltip"
DOM_CHANCE_BREAKDOWN_TOOLTIP = "dom_chance_breakdown_tooltip"
ROOT_STAMINA_TOOLTIP = "root_stamina_tooltip"
PARTNER_STAMINA_TOOLTIP = "partner_stamina_tooltip"

CANCEL_MEETING_OPTION = "cancel_meeting_option"
CANCEL_MEETING_TOOLTIP = "cancel_meeting_tooltip"
CANT_DOM_DUE_TO_CUM_TOOLTIP = "cant_dom_due_to_cum_tooltip"
EASY_DOM_DUE_TO_CUM_TOOLTIP = "easy_dom_due_to_cum_tooltip"

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
RESET_STAMINA_AFTER_CUM_EFFECT = "reset_stamina_after_cum_effect"
ROOT_CUM = "root_cum"
PARTNER_CUM = "partner_cum"
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
NEXT_EVENT = "next_event"
SAVED_EVENT_ID = "saved_event_id"

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
THEM_FULL_REGNAL = "[affairs_partner.GetFullNameRegnal]"
ME_FULL_REGNAL = "[ROOT.Char.GetFullNameRegnal]"
ME_NAME = "[ROOT.Char.GetFirstName]"
ME_LADY_LORD = "[ROOT.Char.GetLadyLord]"  # Idk how to get this to just take the first title (Baroness/Duchess/Queen/etc.)

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
