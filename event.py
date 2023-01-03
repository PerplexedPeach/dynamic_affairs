from defines import *
from util import clean_str, event_type_namespace
import copy


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
                 # similarly for partner
                 partner_cum_text=None,
                 # overrides the standard gender pairing rules for deciding whose stamina ends the scene
                 # None means no override, True means root's stamina will be used while False means the partner
                 force_root_stamina_finishes=None,
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
        if root_cum_text is not None:
            if isinstance(root_cum_text, str):
                desc = Desc(root_cum_text)
            desc.suffix = "root_cum"
            desc.desc += "\\n"
            self.root_cum_text = desc

        self.partner_cum_text = partner_cum_text
        if self.partner_cum_text is not None:
            if isinstance(partner_cum_text, str):
                desc = Desc(partner_cum_text)
            desc.suffix = "partner_cum"
            desc.desc += "\\n"
            self.partner_cum_text = desc

        self.force_root_stamina_finishes = force_root_stamina_finishes

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

            with Block(self, AFTER):
                self.generate_after()

        return "\n".join(self._lines)

    def root_stamina_decides_finish(self):
        """Whether sex scene ends when root character's stamina reaches 0, or if it's dependent on the partner"""
        if self.force_root_stamina_finishes is not None:
            return self.force_root_stamina_finishes
        elif self.root_gender == FEMALE and self.partner_gender == MALE:
            return False
        elif self.root_gender == MALE and self.partner_gender == FEMALE:
            return True
        elif self.root_gender == FEMALE and self.partner_gender == FEMALE:
            return False
        elif self.root_gender == MALE and self.partner_gender == MALE:
            return False
        raise RuntimeError(f"Unexpected gender pairing root: {self.root_gender} and partner: {self.partner_gender}")

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

    def _generate_finisher_stamina_effect(self):
        # should be called near the top of effects, right after changing root and partner stamina
        if self.root_stamina_decides_finish():
            self.save_scope_value_as(FINISHER_STAMINA, ROOT_STAMINA)
        else:
            self.save_scope_value_as(FINISHER_STAMINA, PARTNER_STAMINA)

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

    def generate_after(self):
        self.assign(RESET_STAMINA_AFTER_CUM_EFFECT, YES)

    def generate_hidden_opinion_change_effect(self, change):
        with Block(self, CHANGE_SUBDOM_EFFECT):
            self.assign(CHANGE, change)

    def filter_repeat_option_from_options(self, options_list):
        # if we have a Repeat event always make that a choice
        non_repeat_options = []
        repeat_option = None
        for option in options_list:
            if isinstance(option.next_event, RepeatedSex) and self.id != option.next_id:
                repeat_option = option
            else:
                non_repeat_options.append(option)
        return non_repeat_options, repeat_option

    def generate_options_transition(self, options_list, option_transition_str):
        options_list, _ = self.filter_repeat_option_from_options(options_list)
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
                                self.add_line(f"{SCOPE}:{FINISHER_STAMINA} <= 0")
                            else:
                                self.add_line(f"{SCOPE}:{FINISHER_STAMINA} > 0")
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
            lines.append(self.root_cum_text.generate_localization(self))
        if self.partner_cum_text is not None:
            lines.append(self.partner_cum_text.generate_localization(self))
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
                self.add_line(f"{ROOT_STAMINA} <= 0")
                # depending on if we have a special root cum text or if we need to default
            if self.root_cum_text is not None:
                self.root_cum_text.generate_desc(self)
            else:
                self.assign(DESC, f"{ROOT_CUM}_{prefix}")

    def generate_partner_cum_desc(self):
        prefix = self.partner_gender
        with Block(self, TRIGGERED_DESC):
            with Block(self, TRIGGER):
                self.add_line(f"{PARTNER_STAMINA} <= 0")
                # depending on if we have a special root cum text or if we need to default
            if self.partner_cum_text is not None:
                self.partner_cum_text.generate_desc(self)
            else:
                self.assign(DESC, f"{PARTNER_CUM}_{prefix}")

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
        self._generate_finisher_stamina_effect()
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
        super(First, self).__init__(*args, **kwargs)
        # generate options to each sex source event
        options = []
        for event in source_sex_events:
            if event.root_gender == self.root_gender and event.partner_gender == self.partner_gender:
                options.append(Option(event.id, OptionCategory.OTHER, event.title))
        self.options = options

    def generate_immediate_effect(self):
        self._generate_finisher_stamina_effect()
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

    def generate_after(self):
        self.assign(CUSTOM_TOOLTIP, ROOT_STAMINA_TOOLTIP)
        self.assign(CUSTOM_TOOLTIP, PARTNER_STAMINA_TOOLTIP)
        super(Sex, self).generate_after()

    def generate_desc(self):
        self.generate_incoming_options_desc()
        super(Sex, self).generate_desc()

    def generate_immediate_effect(self):
        with Block(self, LIDA_ONGOING_SEX_EFFECT):
            self.assign(STAMINA_COST_1, self.stam_cost_1)
            self.assign(STAMINA_COST_2, self.stam_cost_2)

        self._generate_finisher_stamina_effect()

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

    def generate_single_option(self, option: Option, root_cum_terminates, categories_to_options):
        self.add_debug_comment(str(option))
        self.assign(NAME, option.fullname)
        if option.tooltip is not None:
            self.assign(CUSTOM_TOOLTIP, f"{option.fullname}.tt")

        with Block(self, TRIGGER):
            if option.category in [OptionCategory.DOM, OptionCategory.SUB]:
                # non-cum options are only available if finisher is not cumming
                if not isinstance(option.next_id, EventsCum):
                    self.add_line(f"{SCOPE}:{FINISHER_STAMINA} > 0")
                trans_type = DOM_TRANSITION if option.category == OptionCategory.DOM else SUB_TRANSITION
                with Block(self, OR):
                    for choice in range(max_options_per_type):
                        self.assign(f"{SCOPE}:{trans_type}_{choice}", option.id)

        # save this event
        self.save_scope_value_as(PREV_EVENT, self.id.value)
        # for dom options, it could backfire and get you more dommed
        if option.category == OptionCategory.DOM:
            self.generate_dom_option_effect(option, categories_to_options[OptionCategory.SUB])
            if root_cum_terminates:
                # partner cumming makes dom easier
                with Block(self, IF):
                    with Block(self, LIMIT):
                        self.add_line(f"{PARTNER_STAMINA} <= 0")
                    self.assign(CUSTOM_TOOLTIP, EASY_DOM_DUE_TO_CUM_TOOLTIP)
                    self.assign(ADD_INTERNAL_FLAG, SPECIAL)
            else:
                # cumming decreases dom success
                with Block(self, IF):
                    with Block(self, LIMIT):
                        self.add_line(f"{ROOT_STAMINA} <= 0")
                    self.assign(CUSTOM_TOOLTIP, CANT_DOM_DUE_TO_CUM_TOOLTIP)
                    self.assign(ADD_INTERNAL_FLAG, DANGEROUS)
        elif option.category == OptionCategory.SUB:
            self.generate_sub_option_effect(option)
        else:
            raise RuntimeError(f"Unsupported option category {option.category}")

    def generate_options(self):
        categories_to_options = {c: [] for c in OptionCategory}
        options, repeat_option = self.filter_repeat_option_from_options(self.options)

        for option in options:
            categories_to_options[option.category].append(option)

        root_cum_terminates = self.root_stamina_decides_finish()
        # always an option to repeat itself
        if repeat_option is not None:
            with Block(self, OPTION):
                self.generate_single_option(repeat_option, root_cum_terminates, categories_to_options)
                self.assign(ADD_INTERNAL_FLAG, SPECIAL)
        for option in options:
            with Block(self, OPTION):
                self.generate_single_option(option, root_cum_terminates, categories_to_options)

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
            # breakdown of all that contributes to the percentage
            self.assign(CUSTOM_TOOLTIP, DOM_CHANCE_BREAKDOWN_TOOLTIP)

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


class RepeatedSex(Sex):
    """Class for representing repeated choice of an event"""

    def __init__(self, *args, base_event: Sex = None, **kwargs):
        super(RepeatedSex, self).__init__(*args, **kwargs)
        has_option_to_this = False
        non_repeat_options = []
        for o in base_event.options:
            # convert this option to point towards us, so can either define that option as pointing to itself or to us
            if o.next_id == base_event.id:
                o.next_id = self.id
                has_option_to_this = True
            elif o.next_id == self.id:
                has_option_to_this = True
            else:
                non_repeat_options.append(copy.copy(o))
        if not has_option_to_this:
            raise RuntimeError(f"{base_event.id} base event needs an option pointing to itself or {self.id}")
        # inherit all non-looping out-going options
        self.options = list(self.options) + non_repeat_options
        # inherit certain options from base event if they're not specified when constructing this event
        self.root_gender = base_event.root_gender
        self.partner_gender = base_event.partner_gender
        if 'root_cum_text' not in kwargs:
            self.root_cum_text = base_event.root_cum_text
        if 'partner_cum_text' not in kwargs:
            self.partner_cum_text = base_event.partner_cum_text
        if 'force_root_stamina_finishes' not in kwargs:
            self.force_root_stamina_finishes = base_event.force_root_stamina_finishes
        if 'root_become_more_sub_chance' not in kwargs:
            self.root_become_more_sub_chance = base_event.root_become_more_sub_chance
        if 'root_become_more_dom_chance' not in kwargs:
            self.root_become_more_dom_chance = base_event.root_become_more_dom_chance
        if 'animation_left' not in kwargs:
            self.anim_l = base_event.anim_l
        if 'animation_right' not in kwargs:
            self.anim_r = base_event.anim_r
        if 'theme' not in kwargs:
            self.theme = base_event.theme
        if 'stam_cost_1' not in kwargs:
            self.stam_cost_1 = base_event.stam_cost_1
        if 'stam_cost_2' not in kwargs:
            self.stam_cost_2 = base_event.stam_cost_2


class Desc:
    def __init__(self, desc, subid=0, suffix=None):
        self.desc = clean_str(desc)
        self.subid = subid
        self.suffix = suffix

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

    def _generate_full_id(self, b: Event = None, o: Option = None):
        ids = []
        if o is not None:
            ids.append(f"{SEX_TRANSITION}_{o.id}")
        elif b is not None:
            ids.append(b.fullname)
            ids.append(DESC)
        else:
            raise RuntimeError("Need to be a description of either an event or option")
        if self.suffix is not None:
            ids.append(self.suffix)
        ids.append(str(self.subid))
        return ".".join(ids)

    def _generate_desc_event(self, b: Event):
        b.assign(DESC, self._generate_full_id(b=b))

    def _generate_localization_event(self, b: Event):
        return f"{self._generate_full_id(b=b)}: \"{self.desc}\""

    def _generate_desc_option(self, b: Event, o: Option):
        b.assign(DESC, self._generate_full_id(o=o))

    def _generate_localization_option(self, o: Option):
        return f"{self._generate_full_id(o=o)}: \"{self.desc}\""


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
