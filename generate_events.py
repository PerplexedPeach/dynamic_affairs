import argparse
import subprocess

from defines import *
from event import BlockRoot, Block, Event, Cum, First, Sex, OptionCategory, Option, TriggeredDesc, ComposedDesc, \
    Modifier, AddModifier, RepeatedSex
from util import event_type_namespace


class EventMap:
    def __init__(self):
        self.events: typing.Dict[EventId, Event] = {}

    def add(self, event: Event):
        if event.id in self.events:
            raise RuntimeError(f"Trying to re-add {event.id}")
        self.events[event.id] = event

    def __getitem__(self, event_id: EventId):
        return self.events[event_id]

    def sex(self, event_id: EventsSex):
        e = self.events[event_id]
        assert isinstance(e, Sex)
        return e

    def all(self):
        return self.events.values()


def link_events_and_options(events: EventMap):
    option_type_to_number = {
        (EventsSex, EventsSex): 0,
        (EventsSex, EventsCum): 1,
        (EventsFirst, EventsSex): 2,
    }
    options = {}
    terminating_options = 0
    # clear some lists to enable recalling this
    for e in events.all():
        e.incoming_options = []
        e.adjacent_options = []
    for e in events.all():
        # counter of number of transitions from this event to that event
        from_this_to_that = {}
        for o in e.options:
            o.from_id = e.id

            if o.next_id is None:
                terminating_options += 1
                o.id = terminating_options
            else:
                this_to_that_id = o.next_id.value * 100 + e.id.value * option_from_to_offset
                number_of_transitions_to_that_event = 0
                if o.next_id in from_this_to_that:
                    number_of_transitions_to_that_event = from_this_to_that[o.next_id]
                else:
                    from_this_to_that[o.next_id] = 0
                from_this_to_that[o.next_id] += 1

                from_event_type = option_type_to_number[(type(o.from_id), type(o.next_id))]

                o.id = this_to_that_id + from_event_type * 10 + number_of_transitions_to_that_event

            # option generate fullname
            o.fullname = f"{OPTION_NAMESPACE}.{o.id}"
            if o.next_id is not None:
                o.next_event = events[o.next_id]
                o.from_event = e
                o.next_event.incoming_options.append(o)
            if o.id in options:
                raise RuntimeError(f"Duplicate option ID: {o.id}")
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
            add_meeting_events(b, events, EventsFirst.FM_MEETING_WITH_SPOUSE_INITIAL,
                               EventsFirst.FM_MEETING_WITH_SPOUSE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_IN_LIST, prisoner_list)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, events, EventsFirst.FM_MEETING_WITH_PRISONER_INITIAL,
                               EventsFirst.FM_MEETING_WITH_PRISONER)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_VASSAL_OR_BELOW_OF, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, events, EventsFirst.FM_MEETING_WITH_LIEGE_INITIAL, EventsFirst.FM_MEETING_WITH_LIEGE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(TARGET_IS_VASSAL_OR_BELOW, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, events, EventsFirst.FM_MEETING_WITH_VASSAL_INITIAL,
                               EventsFirst.FM_MEETING_WITH_VASSAL)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                inside_limit_check_gender(b, FEMALE, MALE)
            add_meeting_events(b, events, EventsFirst.FM_MEETING_WITH_ACQUAINTANCE_INITIAL,
                               EventsFirst.FM_MEETING_WITH_ACQUAINTANCE)

        # M/F Events
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_SPOUSE_OF, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, MALE, FEMALE)
            add_meeting_events(b, events, EventsFirst.MF_MEETING_WITH_SPOUSE_INITIAL,
                               EventsFirst.MF_MEETING_WITH_SPOUSE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_IN_LIST, prisoner_list)
                inside_limit_check_gender(b, MALE, FEMALE)
            add_meeting_events(b, events, EventsFirst.MF_MEETING_WITH_PRISONER_INITIAL,
                               EventsFirst.MF_MEETING_WITH_PRISONER)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(IS_VASSAL_OR_BELOW_OF, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, MALE, FEMALE)
            add_meeting_events(b, events, EventsFirst.MF_MEETING_WITH_LIEGE_INITIAL, EventsFirst.MF_MEETING_WITH_LIEGE)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                b.assign(TARGET_IS_VASSAL_OR_BELOW, AFFAIRS_PARTNER)
                inside_limit_check_gender(b, MALE, FEMALE)
            add_meeting_events(b, events, EventsFirst.MF_MEETING_WITH_VASSAL_INITIAL,
                               EventsFirst.MF_MEETING_WITH_VASSAL)
        with Block(b, ELSE_IF):
            with Block(b, LIMIT):
                inside_limit_check_gender(b, MALE, FEMALE)
            add_meeting_events(b, events, EventsFirst.MF_MEETING_WITH_ACQUAINTANCE_INITIAL,
                               EventsFirst.MF_MEETING_WITH_ACQUAINTANCE)

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

    # organize events into gender pairings
    pairings = [(FEMALE, MALE), (MALE, FEMALE), (FEMALE, FEMALE), (MALE, MALE)]
    for pairing in pairings:
        these_events = EventMap()
        for event in events.all():
            if event.root_gender == pairing[0] and event.partner_gender == pairing[1]:
                these_events.add(event)

        if len(these_events.events) == 0:
            continue

        suffix = f"{pairing[0]}{pairing[1]}"

        gv_filename = f"vis_{suffix}.gv"
        with open(gv_filename, "w") as f:
            f.write("digraph G {\n")
            if horizontal:
                f.write("rankdir=LR;\n")
            f.write("fontname=Helvetica;\n")
            # merge edges going back and forth - not good since we need different colors
            # f.write("concentrate=true;\n")
            f.write("compound=true;\n")

            f.write(
                f"subgraph cluster_{suffix} "
                f"{{\n label=\"{pairing[0].upper()}/{pairing[1].upper()} Events\";\n")
            # f.write("style=filled;\n fillcolor=\"#f2f0ae\";\n")

            source_sex_events = get_source_sex_events(these_events)
            cum_events = []
            regular_sex_events = []
            first_events = []
            for event in these_events.all():
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
            f.write(f"subgraph cluster_sex_source_{suffix} {{\n label=\"Source\";\n rank=same;\n")
            # invisible node for others to connect to the cluster as a whole
            for i, event in enumerate(source_sex_events):
                f.write(event.id.name)
                f.write(get_event_attr(event))
                f.write(";\n")
            f.write("}\n")

            f.write(f"subgraph cluster_meeting_{suffix} {{\n label=\"Start Meeting Events\";\n rank=source;\n")
            f.write("style=filled;\n fillcolor=\"#A5FFC7\";\n")
            for i, event in enumerate(first_events):
                f.write(event.id.name)
                f.write(get_event_attr(event))
                f.write(";\n")
                # create visual connection between the start meeting events and the source events
                if i == len(first_events) // 2:
                    other = source_sex_events[len(source_sex_events) // 2]
                    f.write(f"{event.id.name} -> {other.id.name} [ltail=cluster_meeting_{suffix},"
                            f"lhead=cluster_sex_source_{suffix}];\n")
            f.write("}\n")

            # cum events (sink nodes)
            f.write(f"subgraph cluster_cum_{suffix} {{\n label=\"Terminal Events\";\n rank=sink;\n")
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
                    if isinstance(option.next_id, EventsCum):
                        attr.append("style=dotted")

                    attr.append(f"penwidth={option.weight / 5}")

                    if len(attr) > 0:
                        attr = "[" + ",".join(attr) + "]"
                        f.write(attr)
                    f.write(";\n")

            f.write("}\n")

            f.write("}\n")

        subprocess.run(["dot", "-Tpng", gv_filename, "-o", f"vis_{suffix}.png"])


# separate sex events so it's easier to navigate in an IDE (can collapse each function)
def define_sex_events_fm(es: EventMap):
    es.add(Sex(EventsSex.FM_WHIP_TEASE, "Whip Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
               With a malevolent smirk at {THEM}, you eye the sizable bulge in their clothing.  
               Pulling a length of your clothing off, you whip it against his covered erection and he stumbles, gasping in pain and pleasure.
               \\n\\n
               Tracing your fingers against his trouser and over his belt, you pull his staff free. It hangs in the brisk air.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Whip him off",
                          transition_text="You run the length of cloathing against his shaft, building a rhythm as he gasps.",
                          failed_transition_text="You're too aroused to be satisfied with just teasing."),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your hands",
                          transition_text=f"""
                          Looking up, anticipation fills {THEM}'s face.
                          They move a hand to cup your cheek, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.FM_FOOTJOB_TEASE, "Footjob Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
               With a heady rush you notice {THEM} has a sizable erection in their clothing.  
               Sliding closer to him, you viciously knee him in the groin. He stumbles and lands on his back, gasping in pain.  
               \\n\\n
               You daintily remove your shoes, and whisper your commands to him.
               Tracing your feet against his trouser, you pull his staff free. It presses against your feet, ticking them in the brisk air.
               """,
               options=(
                   Option(EventsSex.FM_FOOTJOB, OptionCategory.DOM,
                          "Rub him off",
                          transition_text="You rub his thickness between your feet, watching as he flushes and moans.",
                          failed_transition_text="You're too aroused to be satisfied with just teasing."),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your hands",
                          transition_text=f"""
                          Looking up, anticipation fills {THEM}'s face.
                          He moves to rise, but you drive him back down."""),
               )))
    # TODO footjob definition
    es.add(Sex(EventsSex.FM_FOOTJOB, "Footjob",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
               placeholder
               """,
               options=(
                   Option(EventsSex.FM_FOOTJOB, OptionCategory.DOM,
                          "Rub him off",
                          transition_text="placeholder",
                          failed_transition_text="placeholder"),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your hands",
                          transition_text=f"""placeholder"""),
               )))
    es.add(Sex(EventsSex.FM_HANDJOB_TEASE, "Handjob Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
               With a knowing smirk at {THEM}, you put your hands on their chest. 
               Leveraging your weight, you pin him against a wall and slide a knee up his leg. His face reddens as you press against his bulge. 
               \\n\\n
               Tracing your fingers against thin fabric, you work your way to his trouser and pull his staff free. It twitches at sensations of the brisk air and your warm hands.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Jerk him off",
                          transition_text="Your continue building a rhythm going up and down his shaft with your hands.",
                          failed_transition_text="You're too turned on to be satisfied with just jerking him off."),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""
                          Looking up, anticipation fills {THEM}'s face.
                          They move a hand to place behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.FM_PUSSY_TEASE, "Pussy Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
                   Looking into {THEM}'s leering eyes, you know you hold the lead for now.
                   Closing in, you lean close to her ear and promise, "This will be a day you'll remember."
                   \\n\\n
                   Simultaneously, you reach down and pull up her dress, you press closer, and your hands play across her body. Entranced your masculine wiles and seductive manner. She loosens your trousers and pulls your member free. She sucks in a tight breath slide your cock between her thighs and rub your rod against her pussy.""",
               options=(
                   Option(EventsSex.FM_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing her ass and breasts",
                          transition_text=f"""
                              You continue to rub his rod in between your things and pussy. You can feel a sticky coolness
                              from {THEM}'s tip, slicking between your legs. The contrast with the rhythmic thrusts from his 
                              hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it."),
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Slide your fingers within her flower and start stroking",
                          transition_text=f"""
                              Feeling a change of pace, you switch to using your hands to get her off.""",
                          failed_transition_text=f"""
                              She recognizes what you are trying to do and twists her body to avoid having your fingers
                              fully within her womanhood."""),
                   Option(EventsSex.FM_MISSIONARY, OptionCategory.SUB,
                          "Relax and let him do the thrusting along your crack",
                          transition_text=f"""
                              {THEM} wastes no time after you slow down to pick up the pace, his rod now doing the
                              thrusting into your cunt."""),
                   Option(EventsCum.FM_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over on your groin",
                          subdom_sub=0,
                          transition_text=f"""
                              You feel his dick twitch between your thighs and pussy, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.FM_TIT_TEASE, "Tits Tease",
               stam_cost_1=0, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               animation_left=IDLE, animation_right=PERSONALITY_CONTENT,
               desc=f"""
                   Looking into {THEM}'s leering eyes, you know you hold the lead for now.
                   Closing in, you lean close to his ear and promise, "This will be a day you'll remember."
                   \\n\\n
                   Simultaneously, you kneel before him and open your dress, revealing your breats. You bend down and loosen his trousers. His member springs out. Enjoying the moment, you slid his dick against your chest and between your tits. 
                   He sucks in a delighted breath as your tits rub against cock as his hands play across your body.
                   """,
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Jerk him off",
                          transition_text="You continue building a rhythm back and across his shaft with your breats.",
                          failed_transition_text="You're too turned on to be satisfied with just jerking him off."),
                   Option(EventsSex.FM_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and take him in your mouth",
                          transition_text=f"""
                          Looking up, anticipation fills {THEM}'s face.
                          They move a hand to place behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.FM_HANDJOB, "Handjob",
               stam_cost_1=-0.5, stam_cost_2=1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               partner_removes_clothes=True,
               desc=f"""
                   {THEM}'s eyes are closed and you delight in your control of his pleasure.
                   A thrill fills you at the pleasure on his face.""",
               options=(
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Continue jerking him off",
                          transition_text=f"""
                              Under the interminable strokes, {THEM}'s cock hardens.
                              Dew-like pre-cum dribbles from the tip, lubricating the whole shaft.""",
                          failed_transition_text=
                          ComposedDesc(
                              TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", """
                                 You're too turned on to be satisfied with just jerking him off!"""),
                              TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                                  {THEM} wants more than you teasing him, so he #sub takes#! something #italic wetter#!."""),
                              "."
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
                              You place your palm below his cock, ready to receive his seed.""",
                          failed_transition_text=f"""
                              You place your palm below his cock, ready to receive his seed,
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
               root_gender=FEMALE, partner_gender=MALE,
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
                   Option(EventsSex.FM_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Give his member a #italic wetter#! hole",
                          transition_text=ComposedDesc(
                              TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", """
                               You're too turned to just suck him off! You turn around and bend over, making him an offer he #S can't#! refuse."""),
                              TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                               "Your mouth just isn't enough!" he says as he turns you around and bends you over."""),
                              "."
                          ),
                          ),
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
    # TODO define these repeated events
    es.add(RepeatedSex(EventsSex.FM_BLOWJOB_DOM_I, "Dom Blowjob I", base_event=es.sex(EventsSex.FM_BLOWJOB_DOM),
                       root_become_more_dom_chance=5,
                       desc=f"""
                       placeholder""",
                       options=(
                           Option(EventsSex.FM_BLOWJOB_DOM_II, OptionCategory.DOM,
                                  "Continue milking his cock with your lips and tongue",
                                  transition_text=f"""
                              You continue to bob your head back and forth, occasionally glancing up and making adjustments
                              based on their expression. The fact that you have total control over {THEM}'s pleasure makes
                              you excited.""",
                                  failed_transition_text=f"""
                              The incessant invasion of his member down your throat
                              momentarily puts you in a trance, leaving the initiative in his hands.""",
                                  ),
                       )))
    es.add(RepeatedSex(EventsSex.FM_BLOWJOB_DOM_II, "Dom Blowjob II", base_event=es.sex(EventsSex.FM_BLOWJOB_DOM_I),
                       root_become_more_dom_chance=5,
                       desc=f"""
                       placeholder""",
                       options=(
                           Option(EventsSex.FM_BLOWJOB_DOM_II, OptionCategory.DOM,
                                  "Continue milking his cock with your lips and tongue",
                                  transition_text=f"""
                              You continue to bob your head back and forth, occasionally glancing up and making adjustments
                              based on their expression. The fact that you have total control over {THEM}'s pleasure makes
                              you excited.""",
                                  failed_transition_text=f"""
                              The incessant invasion of his member down your throat
                              momentarily puts you in a trance, leaving the initiative in his hands.""",
                                  ),
                       )))
    es.add(Sex(EventsSex.FM_BLOWJOB_SUB, "Sub Blowjob",
               stam_cost_1=1.0, stam_cost_2=1.5,
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=5,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
                   Looking into {THEM}'s leering eyes, you can see her desire to have you.
                   You may not let them have their way with you, but for now you play along.
                   Closing in, you lean close to his ear and promise, "This will be a day you'll remember."
                   \\n\\n
                   Simultaneously, you reach down and loosen her trousers and undergarments,
                   clearly incensed from your masculine wiles and seductive manner. In reciprocation, she pulls
                   down your pants, and you teasingly shake your shapely behind and semi full staff and giving her eyes
                   a treat. You continue shaking while backing up until her groin is pressed against your ass.
                   """,
               options=(
                   Option(EventsSex.FM_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing him with your back",
                          transition_text=f"""
                              You continue to rub your hands across her back behind you, as she kisses your back and neck, wrapping her hands around your waist.
                              You feel the supplness of {THEM}'s breasts, pressed against your back. The contrast with the rhythmic thrusts from his 
                              hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it."),
                   Option(EventsSex.FM_HANDJOB, OptionCategory.DOM,
                          "Slide your fingers within her flower and start stroking",
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
               root_gender=FEMALE, partner_gender=MALE,
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
                          "Slide your fingers within her flower and start stroking",
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
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
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
                              You move to pull away from his fingers, but are stopped
                              by a particularly #bold deep#! thrust scraping your inner walls."""),
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
               root_gender=FEMALE, partner_gender=MALE,
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
                              and pulls you back, giving you a few sharp thrusts as punishment for trying to escape."""),
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
                              "Pull it out, {THEM}!", you manage to voice between his wild thrusts and loud groans.""",
                          failed_transition_text=f"""
                              "Pull it out, {THEM}!", you manage to voice between his wild thrusts and loud groans, but your pleas falls on deaf ears."""),
                   Option(EventsCum.FM_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let him fill you with his seed",
                          transition_text=f"""
                              Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),
               )))
    es.add(Sex(EventsSex.FM_REVERSE_COWGIRL, "Ride Facing Away",
               stam_cost_1=3, stam_cost_2=1.5,
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_dom_chance=10,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
                   You look in {THEM}'s eyes as you vigorously ride, his member under your complete control as you focus exclusively on satisfying yourself. \\n
                   """, TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   He is a tool, his "manhood" nothing more than a meat toy whose #dom only#! purpose is to satisfy your needs. He is a #bold good#! tool.
                   """), TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                   Despite how good this feels you can't help but wish #sub he#! pleasured you instead.  
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
               root_gender=FEMALE, partner_gender=MALE,
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
                   Option(EventsCum.FM_CREAMPIE_BREED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                              His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))
    es.add(Sex(EventsSex.FM_PRONE_BONE, "Lie Face Down",
               stam_cost_1=3.5, stam_cost_2=2.5,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_sub_chance=15,
               animation_left=FLIRTATION_LEFT, animation_right=FLIRTATION_LEFT,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
                   You are face down with your legs closed while {THEM} thrusts deep in your moist womb, your mind melting from the echoing sound of
                   #bold your cheeks getting clapped#! as each #italic ravaging#! stroke sends #sub paralyzing#! jolts of pleasure through your whole being. \\n\\n
                   He's in complete control of your body and mind
                   """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                    and you're enjoying #sub every#! single moment of his cock #italic splitting you in half#!"""),
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
                   Option(EventsCum.FM_CREAMPIE_BREED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                              His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))


def define_sex_events_mf(es: EventMap):
    # to do adapt these to the MF perspective (they are copied from F/M)
    es.add(Sex(EventsSex.MF_WHIP_TEASE, "Whip Tease",
               stam_cost_1=1, stam_cost_2=0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               animation_left=PERSONALITY_CONTENT, animation_right=IDLE,
               desc=f"""
               With a devious smirk, you remove your belt and run it against the skin of {THEM}.
               Leveraging your weight, you push and trap her against a wall. You teasingly whip your belt against their clothed ass
               as your free hand wanders across her body. 
               \\n\\n
               Tracing your fingers against your thin fabric, you pull your trousers down and 
               free your member. It twitches at the brisk air.
               """,
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Jerk her off",
                          transition_text="Your continue building a rhythm, whipping her and fingering her.",
                          failed_transition_text="You're too turned on to be satisfied with just teasing her."),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and suck upon her pussy.",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          She moves a hand behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.MF_FOOTJOB_TEASE, "Footjob Tease",
               stam_cost_1=1, stam_cost_2=0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               animation_left=PERSONALITY_CONTENT, animation_right=IDLE,
               desc=f"""
               With a lascivious smirk, you remove your shoes and run your hands against the skin of {THEM}.
               Leveraging your weight, you push down and trap her against the floor. You teasingly trace your bare feet against her legs and groin
               as your free hand wanders across her body. 
               \\n\\n
               Tracing your fingers against thin fabric, you pull your trousers down 
               to free your member. It twitches at the brisk air.
               """,
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Jerk her off",
                          transition_text="Your continue building a rhythm, rubbing against her and fingering her.",
                          failed_transition_text="You're too turned on to be satisfied with just fingering her."),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and suck upon her pussy.",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          She moves a hand behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.MF_HANDJOB_TEASE, "Finger Tease",
               stam_cost_1=1, stam_cost_2=0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               animation_left=PERSONALITY_CONTENT, animation_right=IDLE,
               desc=f"""
               With a knowing smirk, you size {THEM} up and put both your hands on their breasts.
               Leveraging your weight, you push and trap her against a wall. You slide your knee up her leg 
               and play with her groin. 
               \\n\\n
               Tracing your fingers against thin fabric, you work your way to her dress and pull it from her body.
               Her skin twitches at the brisk air and the sharp contrast against of your warm hands.
               """,
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Jerk her off",
                          transition_text="Your continue building a rhythm, teasing her and fingering her.",
                          failed_transition_text="You're too turned on to be satisfied with just fingering her."),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and suck upon her pussy.",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          She moves a hand behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.MF_DICK_TEASE, "Dick Tease",
               stam_cost_1=1, stam_cost_2=0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               animation_left=PERSONALITY_CONTENT, animation_right=IDLE,
               desc=f"""
               With a lusty smirk, you size {THEM} up and put both your hands on their chest, playing with their brests.
               Leveraging your weight, you push and trap her against a wall. Kissing her neck, you feel her pulse quicken. 
               \\n\\n
               Tracing your fingers against thin fabric, you work your cock free and rub it against the opening of her pussy.
               She moans in desire as your warm hands and engorged dick fill her with desire.""",
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Jerk her off",
                          transition_text="Your continue building a rhythm, teasing her and fingering her.",
                          failed_transition_text="You're too turned on to be satisfied with just teasing her."),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and suck upon her pussy.",
                          transition_text=f"""
                          Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          She moves a hand behind your head, but you swat it away."""),
               )))
    es.add(Sex(EventsSex.MF_HANDJOB, "Hand Tease",
               stam_cost_1=-1, stam_cost_2=0.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True,
               desc=f"""
                   {THEM}'s eyes are closed and you smirk at your total control of her pleasure.
                   You experiment with your strokes, and delight at the immediate feedback on her face.""",
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Continue jerking her off",
                          transition_text=f"""
                              Under the interminable strokes from your hand, {THEM}'s pussy has 
                              begun to swell and moisten. Dew-like fluid dribbles from the opening, lubricating her depths.""",
                          failed_transition_text=
                          ComposedDesc(
                              TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", """
                                 You're too turned on to be satisfied with just fingering her!"""),
                              TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                                  {THEM} wants more than your hands, so she #sub takes#! something #italic wetter#!."""),
                              "."
                          ),
                          ),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.SUB,
                          "Kneel down and suck upon her pussy.",
                          transition_text=f"""Looking up, you spot a look of anticipation on {THEM}'s face. 
                          They were probably not expecting you to volunteer your mouth's service.
                          She moves a hand behind your head, but you swat it away."""),
                   Option(EventsCum.MF_RUINED_ORGASM, OptionCategory.DOM,
                          "Deny his release",
                          transition_text=f"""
                              You abruptly stop your teasing motions and slap her face, 
                              disrupting the build up to her climax.""",
                          failed_transition_text=f"""
                              You move to stop her climax, but realize that she did not last as long as you expected."""),
                   Option(EventsCum.MF_HANDJOB_CUM_IN_HAND, OptionCategory.DOM,
                          "Milk her into your large palms",
                          subdom_sub=0,
                          transition_text=f"""
                              You place your palm below and into her pussy, for the flourishing finale.""",
                          failed_transition_text=f"""
                              You place your palm below and into her pussy, for the flourishing finale,
                              but she seems unable to climax...""",
                          ),
                   Option(EventsCum.MF_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make her coat your face in cum",
                          transition_text=f"""
                              You kiss your lips passionately upon her lower lips and gaze into her eyes, preparing for her to release upon your face.""",
                          ),
               )))
    es.add(Sex(EventsSex.MF_BLOWJOB_DOM, "Dom Head",
               stam_cost_1=2, stam_cost_2=0.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_removes_clothes=True,
               animation_right=KNEEL_RULER_3,
               desc=f"""
                   You explore her flower with your tongue and lips, leaving her yearning for your mouth's full commitment.
                   In this position of power and control over her pleasure, you deny her any movement by interlocking hands.""",
               options=(
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Deny her your mouth, replacing it with your hands",
                          weight=5,
                          transition_text=f"""
                              You give {THEM}'s head a last lick, making sure to drag it out as if expressing your tongue's
                              reluctance to part from it. You replace the warmth of your mouth with the milder warmth of
                              your palms and probing fingers, as your head raises to kiss her sensitive mounds.
                              """,
                          failed_transition_text=f"""
                              The potent musk of her member, inflated by the proximity of your 
                              nose to her groin, strangely captivates you and you lose this opportunity to assert more 
                              dominance."""),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.DOM,
                          "Continue imbibe upon her pussy with your lips and tongue",
                          transition_text=f"""
                              You continue to bob your head back and forth, occasionally glancing up and making adjustments
                              based on their expression. The fact that you have total control over {THEM}'s pleasure thrills you beyond words.""",
                          failed_transition_text=f"""
                              The incessant dribble of her juices down your throat
                              momentarily puts you in a trance, leaving the initiative in her hands.""",
                          subdom_dom_success=0),
                   Option(EventsSex.MF_BLOWJOB_SUB, OptionCategory.SUB,
                          "Let her do the work of thrusting her pelvis against your face",
                          transition_text=f"""
                              Your lips and tongue sore from doing all the work, you decide to let her
                              do pick up the slack. "Onwards now {THEM}, show me your mettle."
                              \\n\\n
                              Instead of wasting words, she places both hands behind your head and starts thrusting."""),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Give her pussy a #italic stiffer#! ride",
                          transition_text=ComposedDesc(
                              TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", """
                               You're too turned to just suck her off! You lay back and let her straddle you, making her an offer she #S can't#! refuse."""),
                              TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                               "Your mouth just isn't enough!" she says as she lays you back and straddles you."""),
                          ),
                          ),
                   # TODO make these options more likely if you are addicted to cum
                   Option(EventsCum.MF_RUINED_ORGASM, OptionCategory.DOM,
                          "Cruelly deny her release",
                          transition_text=f"""
                              You pull back and slap her face, disrupting the build up to her climax.""",
                          failed_transition_text=f"""
                              As you try to pull back, she holds the back of your head with her hands."""),
                   Option(EventsCum.MF_BLOWJOB_CUM_IN_MOUTH_DOM, OptionCategory.SUB,
                          "Driver her wild upon your tongue",
                          transition_text=f"""
                              You prepare to plunge within her wet depths with your dexterous tongue."""),
                   Option(EventsCum.MF_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make her coat your face in cum",
                          transition_text=f"""
                              You kiss your lips passionately upon her lower lips and gaze into her eyes, preparing for her to release upon your face."""),
               )))
    es.add(Sex(EventsSex.MF_BLOWJOB_SUB, "Sub Head",
               stam_cost_1=1.5, stam_cost_2=1.0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=5,
               root_removes_clothes=True,
               animation_right=KNEEL_RULER_3,
               desc=f"""
                   With your tongue out, your mouth receives {THEM}'s rhythmic thrusts. Her hands behind
                   your head prevent you from instinctively pulling away, making you feel self conscious about
                   being kept captive in such a compromising position.""",
               options=(
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.DOM,
                          "Take back control and be the active one giving the head",
                          transition_text=f"""
                              Putting both hands on his waist, you curb her thrusts. 
                              {THEM} moves her arms as if to protest, but your arms press them back, and
                              resolve any nascent objections.""",
                          failed_transition_text=f"""
                              Putting both hands on his waist, you attempt to curb her thrusts.
                              However, on your knees beneath her, you don't have enough leverage to forcefully
                              stop her and she seems to have no intention of letting you back in control.
                              """),
                   Option(EventsSex.MF_BLOWJOB_SUB, OptionCategory.SUB,
                          "Let her continue her thrusts",
                          transition_text=f"""
                              You adjust your posture better suit his thrusts, making sure to service her fully."""),
                   Option(EventsSex.MF_DEEPTHROAT, OptionCategory.SUB,
                          "Let her thrust even deeper",
                          transition_text=f"""
                              She takes advantage of your lack of strong resistance to dominate you, driving you from your knees to your back.
                               Trapping your head with her hands, she plunges more forcefully while you gasp for air."""),
                   Option(EventsCum.MF_HANDJOB_CUM_IN_HAND, OptionCategory.DOM,
                          "Finish her off on your hands",
                          transition_text=f"""
                              Pulling away, you deprive her of the warmth of your mouth.""",
                          failed_transition_text=f"""
                              Try as you might, {THEM} stops you from pulling away."""),
                   Option(EventsCum.MF_BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.SUB,
                          "Let her cum in your mouth",
                          subdom_sub=0,
                          transition_text=f"""
                              You don't resist when she trembles upon your mouth, and her warmth seeps within your mouth."""),
                   Option(EventsCum.MF_BLOWJOB_CUM_ON_FACE, OptionCategory.SUB,
                          "Make her coat your face in cum",
                          subdom_sub=0,
                          transition_text=f"""
                              You don't resist when she trembles upon your face, and her warmth seeps across your eyes and mouth."""),
               )))
    es.add(Sex(EventsSex.MF_DEEPTHROAT, "Supine Head",
               stam_cost_1=2.0, stam_cost_2=1.0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=10,
               root_removes_clothes=True,
               animation_right=KNEEL_2,
               desc=ComposedDesc("""
                   Your eyes tear up as she thrusts relentlessly. The degrading way in which she
                   gives not care about your well-being or pleasure leaves a deep impression on you.""",
                                 TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}", """
                   In a dark part of your mind, though you may not admit it, you enjoy being used like
                   a cheap toy."""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                   You enjoy being used like a cheap toy, reinforcing your submissive nature."""),
                                 ),
               options=(
                   Option(EventsSex.MF_BLOWJOB_SUB, OptionCategory.DOM,
                          "Take some control back",
                          transition_text=f"""
                              Putting both hands on her waist, you reduce her thrusts to a manageable pace. 
                              """,
                          failed_transition_text=f"""
                              Putting both hands on her waist, you push and try to stop her thrusts.
                              It's all in vain, however, as she ignores you.
                              """),
                   Option(EventsSex.MF_DEEPTHROAT, OptionCategory.SUB,
                          "Continue supine head",
                          transition_text=f"""
                              SHe continues fucking your face while 
                              your vision blurs against a mixture of tears, saliva, and sex juices."""),
                   Option(EventsCum.MF_BLOWJOB_CUM_IN_MOUTH_SUB, OptionCategory.SUB,
                          "She cums in your mouth",
                          subdom_sub=0,
                          transition_text=f"""
                              You don't have any say in it, or in anything else at the moment, as her fluids
                              fills your mouth."""),
               )))
    es.add(Sex(EventsSex.MF_ASS_TEASE, "Ass Tease",
               stam_cost_1=0.75, stam_cost_2=0.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
                   Looking into {THEM}'s leering eyes, you can see her desire to have you.
                   You may not let them have their way with you, but for now you play along.
                   Closing in, you lean close to her ear and promise, "This will be a day you'll remember."
                   \\n\\n
                   Spinning her around, you pull up her dress and run your hands across her ass, teasingly kissing her and giving her body gentle tease.
                   Clearly incensed from your masculine wiles and seductive manner, she reaches down and loosens your trousers.
                   You continue exploring her body with your hand and spin her around rubbing your manhood against her ass cheeks.
                   """,
               options=(
                   Option(EventsSex.MF_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing her ass",
                          transition_text=f"""
                              You rub your rod in between her buns. You feel your rod run between her cheeks, as you hold her against you and whisper in {THEM}'s ears. The contrast with the rhythmic thrusts and her clear desire makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that ass than just teasing it."),
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Slide your fingers within her flower and start stroking",
                          transition_text=f"""
                              Feeling a change of pace, you switch to using your hand to get her off.""",
                          failed_transition_text=f"""
                              She recognizes what you are trying to do and twists her body to avoid having her flower filled
                              by your your fingers."""),
                   Option(EventsSex.MF_HOTDOG, OptionCategory.SUB,
                          "Relax and let her do the thrusting along her crack",
                          transition_text=f"""
                              {THEM} wastes no time after you slow down. She picks up the pace, as your rod moves along her 
                              thrusting crack."""),
                   Option(EventsCum.MF_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "You cum on on her cheeks",
                          transition_text=f"""
                              You manage to guide guide stream onto her cheeks.""",
                          failed_transition_text=f"""
                              You try to guide your stream onto her cheeks, but she pulls away, too hard to control"""),
                   Option(EventsCum.MF_CUM_ON_GROIN, OptionCategory.SUB,
                          "Cum all over on her groin",
                          subdom_sub=0,
                          transition_text=f"""
                              You feel your dick twitch between her cheeks, alerting you to your impending climax.""")
               ))) ## CONTINUE HERE 
    es.add(Sex(EventsSex.MF_ASS_RUB, "Ass Rub",
               stam_cost_1=0.75, stam_cost_2=0.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=5,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
                   Despite not being able to see her standing behind you, 
                   you feel a sense of control as you rub her ass and control his pleasure with your ass.
                   """,
               options=(
                   Option(EventsSex.MF_ASS_RUB, OptionCategory.DOM,
                          "Continue teasing him with your ass",
                          transition_text=f"""
                              You continue to rub his rod in between your buns. You can feel a sticky coolness
                              from {THEM}'s tip, slicking up your back. The contrast with the rhythmic thrusts from his 
                              hot member makes this an interesting experience.""",
                          failed_transition_text="You have better uses for that hard cock than just teasing it"),
                   Option(EventsSex.MF_HANDJOB, OptionCategory.DOM,
                          "Slide your fingers within her flower and start stroking",
                          transition_text=f"""
                              Feeling a change of pace, you switch to using your hand to get him off.""",
                          failed_transition_text=f"""
                              He recognizes what you are trying to do and twists his body to avoid having his member
                              fully trapped within your fingers."""),
                   Option(EventsSex.MF_HOTDOG, OptionCategory.SUB,
                          "Relax and let him do the thrusting along your crack",
                          transition_text=f"""
                              {THEM} wastes no time after you slow down to pick up the pace, his rod now doing the
                              thrusting along your crack."""),
                   Option(EventsCum.MF_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                              You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                              You try to guide his stream onto your cheeks, but he is cumming too hard to control"""),
                   Option(EventsCum.MF_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                              You feel his dick twitch between your cheeks, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.MF_HOTDOG, "Get Hotdogged",
               stam_cost_1=0.75, stam_cost_2=0.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=f"""
                   You lay back and relax as his cock repeatedly parts your cheeks. He holds your arms
                   to keep you from sliding away during his thrusts, which you allow.
                   """,
               options=(
                   Option(EventsSex.MF_ASS_RUB, OptionCategory.DOM,
                          "Resume active rubbing to take back some control",
                          transition_text=f"""
                              Having rested a bit by letting him do the thrusting, you restart your own
                              bounce to better control his pleasure.""",
                          failed_transition_text=f"""
                              Having tasted a bit of control, he has no intention of relenting and giving it back to you.
                              """),
                   Option(EventsSex.MF_HOTDOG, OptionCategory.DOM,
                          "Continue to get him off with your ass",
                          dom_success_adjustment=10,
                          transition_text=f"""
                              You enjoy the sensation of controlling his pleasure with just your butt, without having
                              to resort to any penetration.""",
                          failed_transition_text=f"""
                              Your thoughts are occupied by his vigorous thrusts, and you can't help but wonder what it 
                              would feel like to him thrust inside you."""),
                   Option(EventsSex.MF_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Get on top and ride him facing away",
                          dom_success_adjustment=10,
                          transition_text=f"""
                              You push your groin backwards, forcing him to the ground as you get his rod inside you.""",
                          failed_transition_text=f"""
                              You try to force him to the ground, but as you push your groin backwards something
                               #italic enters#! you and {THEM} wraps an arm around your bosom, holding you in place."""),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.DOM,
                          "Switch to using your mouth",
                          dom_success_adjustment=10,
                          transition_text=f"""
                              His vigorous thrusts invade your mind and you can't help but wonder what it would feel like
                              inside of you. You satisfying this curiosity by offering your mouth.""",
                          failed_transition_text=f"""
                              His vigorous thrusts invade your mind and you can't help but wonder what it would feel like
                              inside of you. You won't be satisfied with just him inside your mouth.
                              """),
                   Option(EventsSex.MF_STANDING_FINGERED_FROM_BEHIND, OptionCategory.SUB,
                          "Let him use his fingers",
                          transition_text=f"""
                              As if his earlier thrusting along your ass crack was in preparation, he plunges his fingers
                              into your wet folds, with only a moan as a weak protest from you."""),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Get impaled from behind",
                          transition_text=f"""
                              One of his thrusts, instead of going up, goes in between your thighs. Your wet folds dribble
                              your anticipation onto his cock. Accepting your body's invitation, his next thrust pierces
                              into you, eliciting a moan from your lips."""),
                   Option(EventsCum.MF_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                              You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                              You try to guide his stream onto your cheeks, but he is climaxing too hard to control"""),
                   Option(EventsCum.MF_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                              You feel his dick twitch between your cheeks, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.MF_STANDING_FINGERED_FROM_BEHIND, "Fingered from Behind",
               stam_cost_1=0.5, stam_cost_2=-1,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=5,
               root_removes_clothes=True,
               animation_left=SCHADENFREUDE,
               desc=f"""
                   His finger #sub squelches against your wet folds#! as he extracts juices from your lower lips while
                   extracting moans from your upper lips. Your head leans back and he occasionally takes the liberty
                   of entwining his tongue with yours.""",
               options=(
                   Option(EventsSex.MF_HOTDOG, OptionCategory.DOM,
                          "Pull out to recover from his thrusting",
                          transition_text=f"""
                              You pull away from his devious fingers to get a chance to recover.
                              They accept it, for now, and resume thrusting between your buns.""",
                          failed_transition_text=f"""
                              You try to pull away from his devious fingers, but your endeavour is stopped
                              by a particularly deep thrust scraping your inner walls."""),
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.DOM,
                          "Satisfy him with your mouth",
                          dom_success_adjustment=5,
                          transition_text=f"""
                              Giving him something else to thrust into, you get on your knees and starting sucking.""",
                          failed_transition_text=f"""
                              You move to pull away from his fingers, but are stopped
                              by a particularly #bold deep#! thrust scraping your inner walls."""),
                   Option(EventsSex.MF_STANDING_FINGERED_FROM_BEHIND, OptionCategory.SUB,
                          "Continue enjoying his deft hands",
                          transition_text=f"""
                              You melt into his hands as you surrender to pleasure."""),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Let him fuck you proper",
                          transition_text=f"""
                              Surrendering to pleasure and wanting more, you involuntarily push your groin backwards, but find
                               #italic something else#! at your entrance. Welcoming the invitation, he plunges into you fully."""),
                   Option(EventsCum.MF_ASS_TEASE_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him cum on your cheeks",
                          transition_text=f"""
                              You manage to guide his stream onto your cheeks.""",
                          failed_transition_text=f"""
                              You try to guide his stream onto your cheeks, but he is climaxing too hard to control"""),
                   Option(EventsCum.MF_CUM_ON_GROIN, OptionCategory.SUB,
                          "Let him cum all over your groin",
                          subdom_sub=0,
                          transition_text=f"""
                              You feel his dick twitch against your ass, alerting you of his impending climax.""")
               )))
    es.add(Sex(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, "Standing Fucked from Behind",
               stam_cost_1=1.5, stam_cost_2=2,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=7,
               root_removes_clothes=True, partner_removes_clothes=True,
               animation_left=SCHADENFREUDE, animation_right=BOW_3,
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
                   Option(EventsSex.MF_BLOWJOB_DOM, OptionCategory.DOM,
                          "Pleasure him with your mouth instead",
                          transition_text=f"""
                              You pull away and recover a bit of control by placing your hands and mouth around
                              his cock, where you can easily decide what to do with it.""",
                          failed_transition_text=f"""
                              You attempt to pull away and recover some control, but you find it hard to focus
                              and pull away from this pleasure."""),
                   Option(EventsSex.MF_BLOWJOB_SUB, OptionCategory.DOM,
                          "Let him fuck your mouth instead",
                          dom_success_adjustment=1,
                          transition_text=f"""
                              Dropping to your knees, you replace the hole he thrusts into. {THEM} don't seem to mind and
                              doesn't break their rhythm.""",
                          failed_transition_text=f"""
                              You attempt to extricate yourself with gravity's assistance. However, he grabs your arms
                              and pulls you back, giving you a few sharp thrusts as punishment for trying to escape."""),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Submit to getting plowed",
                          transition_text=f"""
                              You accept his invasion, each thrust making it harder and harder to pull away and form
                              coherent thoughts. Instead, your mind is filled with a pink haze, urging you to just accept
                              the pleasure of being used like a piece of meat.
                              """),
                   Option(EventsSex.MF_PRONE_BONE, OptionCategory.SUB,
                          "Submit to getting plowed facing down",
                          transition_text=f"""
                              Your legs weaken as you fall to the floor, {THEM} immediately following you down as he 
                              takes advantage of the opportunity to #sub dominate#! you. You try to prepare yourself for 
                              the #bold intense#! pounding that you're about to recieve.
                              """),
                   Option(EventsCum.MF_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                              "Pull it out, {THEM}!", you manage to voice between his wild thrusts and loud groans.""",
                          failed_transition_text=f"""
                              "Pull it out, {THEM}!", you manage to voice between his wild thrusts and loud groans, but your pleas falls on deaf ears."""),
                   Option(EventsCum.MF_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let him fill you with his seed",
                          transition_text=f"""
                              Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),
               )))
    es.add(Sex(EventsSex.MF_REVERSE_COWGIRL, "Ride Facing Away",
               stam_cost_1=1.5, stam_cost_2=3,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=15,
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
                   Option(EventsSex.MF_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Continue riding him",
                          transition_text=f"""
                              You continue riding {THEM} as he is powerlessly lying under you, his rod constantly hitting the insides of your walls.""",
                          failed_transition_text=f"""
                              You try to continue riding him, but as you slow down a moment he grabs you arms and pushes your waist forward.
                              You nearly topple before feeling a burst of pleasure as {THEM}'s cock enters you.
                              """),
                   Option(EventsSex.MF_COWGIRL, OptionCategory.DOM,
                          "Roll around",
                          transition_text=f"""
                              You turn around, meeting {THEM}'s gaze as you continue riding him.""",
                          failed_transition_text=f"""
                              You try to turn around, but your legs feel weak and {THEM} doesn't miss his opportunity to take the lead and guide your next move.
                              """),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.SUB,
                          "Stand up and let him take you from behind",
                          transition_text=f"""
                              You stand up, letting him take you however he desires""", ),
                   Option(EventsSex.MF_PRONE_BONE, OptionCategory.SUB,
                          "Lie on your belly and let him pound you",
                          transition_text=f"""
                              You end up on your belly, readying yourself as {THEM} prepares to pound you.""", ),
                   Option(EventsCum.MF_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Make him pull out and cum on your ass",
                          transition_text=f"""
                              You put your hand on his rod, guiding him to unload on your cheeks instead""",
                          failed_transition_text=f"""
                              You put your hand on his rod, trying to guide him to cum on your cheeks instead, but are suddenly grabbed."""),
                   Option(EventsCum.MF_CREAMPIE_ON_TOP, OptionCategory.DOM,
                          "Pin him down and #bold take#! his seed",
                          transition_text=f"""
                              Your body tightens as he begins to twitch inside you.""",
                          failed_transition_text=f"""
                              Your body tightens as he begins to twitch inside you, but you lose control as he grabs your hips and pulls down on them."""),
                   Option(EventsCum.MF_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let #bold him#! fill you with his seed",
                          transition_text=f"""
                              Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),
               )))
    es.add(Sex(EventsSex.MF_COWGIRL, "Ride Facing Them",
               stam_cost_1=1.0, stam_cost_2=2.0,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=10,
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
                   Option(EventsSex.MF_COWGIRL, OptionCategory.DOM,
                          "Continue riding him",
                          transition_text=f"""
                              You continue riding {THEM}, his rod madly bouncing from wall to wall inside you as if attempting to escape.""",
                          failed_transition_text=f"""
                              You continue riding him, but as you slow down for a moment {THEM} pushes you backwards, trying to get control over you.
                              """),
                   Option(EventsSex.MF_REVERSE_COWGIRL, OptionCategory.DOM,
                          "Roll around",
                          transition_text=f"""
                              You turn your back towards {THEM}, treating him as no more than a piece of meat.""",
                          failed_transition_text=f"""
                              You begin to turn your back towards him, but your legs feel weak and {THEM} doesn't miss his opportunity to take the lead and guide your next move.
                              """),
                   Option(EventsSex.MF_HOTDOG, OptionCategory.SUB,
                          "Pull out to recover from his thrusting",
                          dom_success_adjustment=10,
                          transition_text=f"""
                              {THEM} twitches backwards, managing to get up, as he escapes from under you.""", ),
                   Option(EventsSex.MF_MISSIONARY, OptionCategory.SUB,
                          "Lie on your back and let him pound you",
                          transition_text=f"""
                              You end up on your back, readying yourself as {THEM} lifts your legs, making way for his rod.""", ),
                   Option(EventsCum.MF_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Make him pull out and cum on your ass",
                          transition_text=f"""
                              You put your hand on his rod, guiding him to unload on your cheeks instead""",
                          failed_transition_text=f"""
                              You put your hand on his rod, trying to guide him to cum on your cheeks instead, but are suddenly grabbed."""),
                   Option(EventsCum.MF_CREAMPIE_ON_TOP, OptionCategory.DOM,
                          "Pin him down and #bold take#! his seed",
                          transition_text=f"""
                              Your body tightens as he begins to twitch inside you.""",
                          failed_transition_text=f"""
                              Your body tightens as he begins to twitch inside you, but you lose control as he grabs your hips and pulls down on them."""),
                   Option(EventsCum.MF_CREAMPIE_REGULAR, OptionCategory.SUB,
                          "Let #bold him#! fill you with his seed",
                          transition_text=f"""
                              Feeling little resistance from your body, he prepares to leave you a hot, sticky gift."""),

               )))
    es.add(Sex(EventsSex.MF_MISSIONARY, "Lie on Back",
               stam_cost_1=1.5, stam_cost_2=2,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=10,
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
                   Option(EventsSex.MF_COWGIRL, OptionCategory.DOM,
                          "Roll with him and get on top",
                          transition_text=f"""
                              You grab {THEM} as he's recovering from a thrust and push him sideways with all your strength, landing on top of him.""",
                          failed_transition_text=f"""
                              You grab {THEM} as he's recovering from a thrust and manage to get on your side, but he grabs and puts you back down.
                              """),
                   Option(EventsSex.MF_MISSIONARY, OptionCategory.SUB,
                          "Keep your legs up",
                          transition_text=f"""
                              You keep your legs up, letting {THEM} continue nailing you from above."""),
                   Option(EventsSex.MF_PRONE_BONE, OptionCategory.SUB,
                          "Roll in place, submitting completely",
                          transition_text=f"""
                              You find yourself rolled onto your belly, your opening at {THEM}'s mercy."""),
                   Option(EventsCum.MF_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                              "Not inside!" you barely blurt out between moans and labored breaths.""",
                          failed_transition_text=f"""
                              "Not inside!" you barely blurt out between moans and labored breaths, but your pleas falls on deaf ears."""),
                   Option(EventsCum.MF_CREAMPIE_BREED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                              His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))
    es.add(Sex(EventsSex.MF_PRONE_BONE, "Lie Face Down",
               stam_cost_1=2.5, stam_cost_2=3.5,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=15,
               animation_left=FLIRTATION_LEFT, animation_right=FLIRTATION_LEFT,
               root_removes_clothes=True, partner_removes_clothes=True,
               desc=ComposedDesc(f"""
                   You are face down with your legs closed while {THEM} thrusts deep in your moist womb, your mind melting from the echoing sound of
                   #bold your cheeks getting clapped#! as each #italic ravaging#! stroke sends #sub paralyzing#! jolts of pleasure through your whole being. \\n\\n
                   He's in complete control of you
                   """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                    and you're enjoying #sub every#! single moment of his cock #italic splitting you in half#!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                    and you #dom hate#! having to admit to yourself that he might #italic break#! you"""), "."
                                 ),
               options=(
                   Option(EventsSex.MF_MISSIONARY, OptionCategory.DOM,
                          "Roll in place",
                          transition_text=f"""
                              You find an opening between {THEM}'s thrusts and manage to roll in place, your body now facing his,
                               but he quickly spreads your legs out of the way of his prick.""",
                          failed_transition_text=f"""
                              You try to roll in place, but {THEM}'s #bold paralyzing#! barrage of thrusts never slows enough to do so.
                              """),
                   Option(EventsSex.MF_STANDING_FUCKED_FROM_BEHIND, OptionCategory.DOM,
                          "Get up",
                          transition_text=f"""
                              You find a moment between thrust and pull your knees under you, managing to get up, but {THEM}'s relentless assault
                              continues as he holds your arms while entering you once more.""",
                          failed_transition_text=f"""
                              You try to find a moment to pull your knees under you, but each attempt is thwarted by his wild thrashing."""),
                   Option(EventsSex.MF_PRONE_BONE, OptionCategory.SUB,
                          "Submit to getting #bold mercilessly#! plowed",
                          transition_text=f"""
                              The immense warmth of {THEM} pounding you to the core makes your body melt as your mind is #sub flooded with heat#!.
                              """,
                          ),
                   Option(EventsCum.MF_PULL_OUT_CUM_ON_ASS, OptionCategory.DOM,
                          "Have him pull out and cum on your ass",
                          transition_text=f"""
                              "D-Don't fill me!" you shakingly say as his pounding nearly drives you senseless.""",
                          failed_transition_text=f"""
                              "D-Don't fill me!" you shakingly say as his pounding nearly drives you senseless, but your pleas falls on deaf ears."""),
                   Option(EventsCum.MF_CREAMPIE_BREED, OptionCategory.SUB,
                          "Get #italic filled to the brim#!",
                          transition_text=f"""
                              His rod gets even harder as his relentless pounding reaches your deepest spot, #bold drowning#! your thoughts in euphoria."""
                                          ""),
               )))


def define_sex_events(es: EventMap):
    # define directed graph of events
    define_sex_events_fm(es)
    define_sex_events_mf(es)


def define_cum_events_fm(es: EventMap):
    es.add(Cum(EventsCum.FM_HANDJOB_CUM_IN_HAND, "A Load in Hand is Worth Two in the Bush",
               subdom_change=1, root_become_more_dom_chance=20,
               root_gender=FEMALE, partner_gender=MALE,
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
               "Not bad, {THEM}!", you say while taking note of his #italic potential#! for any possible future encounters.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", """
               "Impressive!", you say as you suck one of your fingers clean, "Maybe use that #sub intensity#! for
                #!italic something else#! next time?"
               """),
                                 )))
    es.add(Cum(EventsCum.FM_ASS_TEASE_CUM_ON_ASS, "Icing on the Cake",
               subdom_change=0,
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
               animation_left=SHAME, animation_right=SCHEME,
               terminal_option=Option(None, OptionCategory.OTHER, "Sample some stray globs of cum"),
               desc=ComposedDesc(f"""
                   You look up and brace yourself for what's to come. When the first drop hits your face,
                   you flinch and instinctively close your eyes and feel a glob hot semen 
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
               root_gender=FEMALE, partner_gender=MALE,
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
               root_gender=FEMALE, partner_gender=MALE,
               animation_left=SHAME, animation_right=SCHADENFREUDE,
               terminal_option=Option(None, OptionCategory.OTHER, "Recover from having your throat used so roughly"),
               desc=ComposedDesc(f"""
                   {THEM} holds your head in place while his last thrust goes deeper than before.
                   His dick twitches and shoots out his seed in a steady stream which fills up your mouth
                   as he makes no move to remove his member. 
                   \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "Swallow it," he says in a commanding tone. \\n\\n
                   """),
                                 """
                                 As you have no choice apart from drowning, you swallow it. As he
                                 thrusted deeply, most of his seed already flowed down your throat.
                                 You #sub gulp audibly and slurp it all down#!.
                                 \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "You look beautiful covered in my cum," {THEM} says while #sub wiping his cock against your face#!.
                   Taking advantage of your helpless state, he takes some liberties in degrading you.
                   \\n\\n
                   """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                   The intensity of his thrust, the force with which he just kept you there... How #sub arousing!#!
                   """, ),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   Seems like {THEM} needs to be #dom put#! in his place, overzealous ruffian that he is. 
                   """, ),
                                 )
               ))
    es.add(Cum(EventsCum.FM_RUINED_ORGASM, "A Firm Grasp on His Release",
               subdom_change=2, root_become_more_dom_chance=35,
               root_gender=FEMALE, partner_gender=MALE,
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
               subdom_change=1,
               root_gender=FEMALE, partner_gender=MALE,
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
    es.add(Cum(EventsCum.FM_CUM_ON_GROIN, "Snowfall on the Bushes",
               subdom_change=-1,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_sub_chance=5,
               preg_chance_1=PREGNANCY_CHANCE * 0.01,
               animation_left=DISMISSAL, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean up the white coating on your groin"),
               desc=ComposedDesc(f"""
                   {THEM} stops himself mere inches from your groin, coating your hips and holes with a thick layer of white. 
                   \\n\\n
                   Your can feel his warmth #sub on#! you.""",
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
                    Ugh, that #dom fool#! made #italic such#! a mess!"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                    If only he'd done #sub more#! to you!"""),
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_REGULAR, "Plowing the Fields",
               subdom_change=-3,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_sub_chance=20,
               preg_chance_1=PREGNANCY_CHANCE,
               animation_left=WORRY, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe away the cum dripping down your thighs"),
               desc=ComposedDesc(f"""
                   "Ugh," {THEM} grunts as he plunges to the hilt, his rod wildly throbbing inside you.
                    As the load overflowing around his rod drips out of you, a white contour remains on your lips.""",
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
                   Your body is brimming with anticipation as you softly say: "Y-you can do it again if you want". You #bold #sub want#!#! him to do it again, \\n"""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                   Is the #dom privilege#! of experiencing your body not enough?! How #dom dare#! he release inside you whenever he wishes
                    like in some #italic random wench?!#!"""),
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_ON_TOP, "Cherry on Top",
               subdom_change=3,
               root_gender=FEMALE, partner_gender=MALE,
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
                   "What are you doing, {ME_NAME}?!", {THEM} says completely stunned.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > 10", f"""
                   "Whatever you need, my {ME_LADY_LORD}!", he says while #dom submitting# to being milked by your womb\\n\\n
                   """),
                                 """You slowly get up, white threads hanging from your slit as drops splash onto the ground. """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   You stare intently into his eyes, knowing he couldn't have stopped you from #dom taking#! his seed no matter how hard he tried - so #dom you did#!.""")
                                 ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_BREED, "Something to Remember Him By",
               subdom_change=-6,
               root_gender=FEMALE, partner_gender=MALE,
               root_become_more_sub_chance=45,
               preg_chance_1=PREGNANCY_CHANCE * 1.5,
               animation_left=WORRY, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER,
                                      "Feel his seed trickle from your slit for the rest of the day"),
               desc=ComposedDesc(
                   f"""
                    {THEM} grunts loudly with a look of utter relief on his face as he unloads in you, pushing further in with each deep thrust
                     - you feel a growing #bold warmth#! begin coating your insides...
                   \\n\\n
                    """,
                   """You lie there panting, a white sliver dripping from your #sub conquered#! slit as his seed #bold fills#! your womb.""",
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                   He plowed you like a cheap whore, his pounding intensifying as he filled you up and you had with #sub no say#! in it.
                    Are you so irresistible that he couldn't help but cum inside """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB} \n {NOT} = {{ {HAS_TRAIT} ={PREGNANT} }}", f"""
                   or is he #italic trying#! to breed you? Either way, you #sub love#! the feeling.""", ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB} \n {HAS_TRAIT} = {PREGNANT}", f"""
                   even with a bun already in you? How #sub flattering#!.""", ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """\\n\\n"""),

                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "M-my {ME_LADY_LORD}!", {THEM} blurts out while staring at your stuffed hole in shock.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 20", f"""
                   "I'll clean it, forgive me!", he pleads as he starts #dom licking#! you clean, having pulled out #S far#! too late.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10 \n{NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }}", f"""
                   \\n"Leave, #dom fool#!!" you say while #warning furiously#! kicking him away from your slit, banishing him bare from your chamber.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10 \n{HAS_TRAIT} = {LIDA_SUB}", f"""
                   \\n"Oh, that's alright" you say while still #sub blushing#! from his #italic sudden#! burst of #bold intense#! vigor.
                   """),

                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "You're #sub mine#! now, {ME_NAME}", {THEM} whispers in your ear before finally beginning to pull out.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -20", f"""
                   You moan sharply as he thrusts in to the hilt one last time, your back #italic arching#! from the sudden
                    jolt of pleasure as your mind #sub gives in#! to the #S heat#! stirring up inside your loins.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10 \n{HAS_TRAIT} = {LIDA_SUB}", f"""
                   \\n\\n"Come again sometime", you say with a #italic #sub smile#!#!. He #sub smacks#! your ass with a grin,
                    running two fingers along your slit before starting to dress.  
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10 \n{NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }}", f"""
                   \\n"Did I say you could #italic do that#!, {THEM}?!". He looks at you with a smug grin, #italic smacking#! your ass before dressing.
                   """),

                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                   \\n\\nAs if getting fucked like a cheap whore wasn't enough, he even #warning seeded#! you like you're just some servant girl at a feast! 
                   """, ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM} \n {NOT} = {{ {HAS_TRAIT} ={PREGNANT} }}", f"""
                   To enjoy the warmth of your womb is an #italic unrivaled privilege#!,
                    how #S #dom dare#!#! he demand more by trying to #S mate with you!?#!
                   """, ),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM} \n {HAS_TRAIT} = {PREGNANT}", f"""
                   Were you not already with child, {THEM} might've #S bred#! you - and you #S #dom loathe#!#! the thought.
                   """, ),

                   TriggeredDesc(
                       f"{NOT} = {{ {HAS_TRAIT} ={PREGNANT} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_DOM} }}",
                       f"""
                   \\n\\nThis isn't #italic quite#! how you were expecting your dalliance to end...
                   """, ),
                   TriggeredDesc(
                       f"{HAS_TRAIT} ={PREGNANT} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_SUB} }} \n {NOT} = {{ {HAS_TRAIT} ={LIDA_DOM} }}",
                       f"""
                   \\n\\nAt least the #italic indiscreet#! ending of this dalliance won't have any #S unwanted#! consequences.
                   """, ),
               ),
               ))
    es.add(Cum(EventsCum.FM_CREAMPIE_KEEP, "Bearing the Bloodline",
               subdom_change=2,
               root_gender=FEMALE, partner_gender=MALE,
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


def define_cum_events_mf(es: EventMap):
    es.add(Cum(EventsCum.MF_HANDJOB_CUM_IN_HAND, "A Load in Hand is Worth Two in the Bush",
               subdom_change=1, root_become_more_sub_chance=20,
               root_gender=MALE, partner_gender=FEMALE,
               terminal_option=Option(None, OptionCategory.OTHER, "Get dressed"),
               animation_left=BOREDOM, animation_right=SHAME,
               desc=ComposedDesc("""
               Your back arches, instinctively thrusting forward to fill an imaginary womb as you spurt your load onto her palms.
               \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
               "Next time I might not #dom go so easy#! on you", you say with a grin as {THEM} looks at her hands.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
               "Not bad, {THEM}!", you say while taking note of her #italic potential#! for any possible future encounters.
               """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
               "Is that it, {ME_NAME}?", she says while wiping her hands on your chest. "How do you hope to please a woman with that stamina?"
               """),
                                 )))
    es.add(Cum(EventsCum.MF_ASS_TEASE_CUM_ON_ASS, "Icing on the Cake",
               subdom_change=0,
               root_gender=MALE, partner_gender=FEMALE,
               terminal_option=Option(None, OptionCategory.OTHER, "Enjoy the view a while"),
               desc=ComposedDesc(f"""
                   As you go past your limit you unleash your warmth on {THEM}'s ass, signaling the end of
                   this session. Some starts tracing a warm path down her legs while the rest stays,
                   a compliment to her curves. #italic Is it normal for you to still be focusing on her body even
                   after sex?#!""",

                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                    #italic Yes, it is - you should have #dom taken#! those cheeks, not just painted them!#!"""),
                                 TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} ={LIDA_DOM} }}", """
                    #italic Perhaps it is, you were #bold so close#! to what you wanted but didn't get it.#!"""),

                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                    \\n\\n"Let's do more next time", you say as you #sub smack her ass#!, surprising her.                  
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                    \\n\\n"Let's meet again sometime, {THEM}" you say while slightly biting your lip.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                    \\n\\n"Thank you for this relief, {ME_FULL_REGNAL}", you say while cleaning her up.
                   """),
                                 ),
               ))
    es.add(Cum(EventsCum.MF_BLOWJOB_CUM_ON_FACE, "Painting her Face",
               subdom_change=2, root_become_more_dom_chance=15,
               root_gender=MALE, partner_gender=FEMALE,
               animation_left=SCHEME, animation_right=SHAME,
               terminal_option=Option(None, OptionCategory.OTHER, "Marvel at your work before dressing"),
               desc=ComposedDesc(f"""
                   You look down and see {THEM} brace herself for what's to come. When you release,
                   she flinchs and instinctively closes her eyes, which was fortunate as one spurt
                   streaks across them.
                   \\n\\n""",

                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "Thank you for this gift, {ME_FULL_REGNAL}" she says while #dom you wipe your cock against her face#!.
                   In her helpless state, you take some liberties in degrading her.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                    "You look great", you remark with a smile as {THEM} opens her eyes slightly flustered.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Impudent knave!" she objects while wiping across her eyeline. "At least have the decency
                   to aim away from my eyes!" she says #italic visibly irritated#!.
                   """),
                                 """\\n\\n""",

                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                    "Next time you're with someone you'll remember this moment, how I marked you, whoever you lay with", you say smugly.
                    {THEM}'s #italic lucky#! you #dom only#! marked her #like this."""),

                                 TriggeredDesc(
                                     f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }} \n {NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}",
                                     f"""
                    "You look great", you remark with a smile as {THEM} opens her eyes slightly flustered.
                   """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                    "Forgive me for the mess, {THEM_FULL_REGNAL}!" you say while trying to clean her up."""),
                                 ))
           )
    es.add(Cum(EventsCum.MF_BLOWJOB_CUM_IN_MOUTH_DOM, "Satisfying her Sweet Tooth",
               subdom_change=1, root_become_more_dom_chance=10,
               root_gender=MALE, partner_gender=FEMALE,
               animation_left=SCHADENFREUDE, animation_right=DISGUST,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe your rod clean"),
               # TODO triggered text depending on cum fetish
               desc=ComposedDesc(f"""
                   You arch your back, holding her head in place with you hands.
                   She moves to free her head, but with your release imminent, you have #dom no intention#! to listen to orders.
                   Soon, your cock twitches in {THEM}'s mouth followed by a series of gulps.
                   """,

                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "You taste so good, {ME_FULL_REGNAL}" she says while licking your rod clean as you enjoy the epilogue of your session.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                    "We ", you remark with a smile as {THEM} opens her eyes slightly flustered.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Impudent knave!" she objects while wiping across her eyeline. "At least have the decency
                   to aim away from my eyes!" she says #italic visibly irritated#!.
                   """),
                                 """\\n\\n""",

                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                    Her mouth is #italic quite#! good... maybe you should take it more often?"""),

                                 TriggeredDesc(
                                     f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }} \n {NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}",
                                     f"""
                    "You look great", you remark with a smile as {THEM} opens her eyes slightly flustered.
                   """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                    "Pardon me, {THEM_FULL_REGNAL}, I shouldn't have!" you say as you abruptly remove yourself from her mouth."""),
                                 )
               ))
    es.add(Cum(EventsCum.MF_BLOWJOB_CUM_IN_MOUTH_SUB, "Down the Gullet",
               subdom_change=-2, root_become_more_dom_chance=20,
               root_gender=MALE, partner_gender=FEMALE,
               animation_left=SCHADENFREUDE, animation_right=SHAME,
               terminal_option=Option(None, OptionCategory.OTHER, "Enjoy the warmth a moment more"),
               desc=ComposedDesc(f"""
                   You hold {THEM}'s head in place while mounting one last thrust even deeper than before.
                   The wet warmth makes you even harder as you begin shooting out seed in a steady stream which fills up her mouth. 
                   \\n\\n""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "Swallow it," you say in a commanding tone. \\n\\n
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Pghl eet aut!," {THEM} says. You look down and inches above your cock see a pair of #italic annoyed#!
                    eyes glaring straight at you. \\n\\n
                   """),
                                 """
                                 As she has no choice apart from drowning, she swallows it. You enjoy the feeling a moment before
                                  you hear and #sub audible gulp#! as she takes it all down.
                                 \\n\\n""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   #dom Using#! her like she's just a warm throat to be plesaed by felt #S great#!. Maybe you'll do it again.
                   """, ),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                   You're not sure #italic where#! this brutality you displayed came from.
                   """, ),

                                 )
               ))
    es.add(Cum(EventsCum.MF_RUINED_ORGASM, "A Firm Grasp on Your Release",
               subdom_change=-2, root_become_more_sub_chance=35,
               root_gender=MALE, partner_gender=FEMALE,
               animation_left=BEG, animation_right=DISMISSAL,
               terminal_option=Option(None, OptionCategory.OTHER, "Leave yearning and frustrated"),
               desc=ComposedDesc(f"""
                   You arche your back as you're clearly about to to climax, but are interrupt by {THEM} firmly grabbing and holding your
                   shaft close to your body. Even if you wanted to, #S and you do#!, you cannot physically cannot release your seed.
                   "Did I say you could cum?" {THEM} cruelly intones as she grasps your balls with your other hand.
                   \\n\\n
                   
                   \\n\\n""",
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   How #dom dare#! she deny you satisfaction. You will not forget this offense.
                   """, ),
                                 TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", f"""
                   "Please, I'm so close," you whine.
                   """, ),
                                 """"You didn't earn it today," she responds, "maybe next time #dom if you please me.#!"""

                                 ),
               custom_immediate_effect=AddModifier(Modifier(SEXUALLY_FRUSTRATED, duration=f"{YEARS} = 1", root=False))
               ))
    es.add(Cum(EventsCum.MF_PULL_OUT_CUM_ON_ASS, "More Icing on the Cake",
               subdom_change=-1,
               root_gender=MALE, partner_gender=FEMALE,
               preg_chance_2=0.05 * PREGNANCY_CHANCE,
               animation_left=PERSONALITY_BOLD, animation_right=FLIRTATION_LEFT,
               root_become_more_sub_chance=10,
               terminal_option=Option(None, OptionCategory.OTHER, "Clean yourself and get dressed"),
               desc=ComposedDesc(
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   Fearing the consequences of impregnating {THEM}, you pull out just before going past your limit.
                   You instead shoots your seed on her ass, several quiet splashes announcing the end of the session.
                   \\n\\n
                   "It is a privilege to satisfy your womb's needs, {THEM_FULL_REGNAL}", you say while devotedly cleaning her up.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                   Perhaps fearing the consequences of impregnating {THEM} or just showing some courtesy, you pull out just as you reache your limit.
                   You instead shoots your seed on her ass and holes, several quiet splashes announcing the end of the session. 
                    \\n\\n
                   "What happens next?", she says while #italic clearly#! staring at your body with a lustful gaze.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   Perhaps out of courtesy or simply not wanting to impregnate {THEM}, you pull out just as you go past his limit.
                   You instead shoots your seed all across her groin, several quiet splashes announcing the end of the session.\\n\\n
                   With a sudden #sub smack on her ass#!, "Let's meet again soon."
                   """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                    \\n\\n"Good boy", {THEM} whispers in your ear while #dom patting#! you on the head. 
                    "I #S might#! just invite you over again if I ever need something", she says with a smirk.
                    """),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                    \\n\\n"Oh, we're doing this again sometime", you say assertively while grabbing her shapes before going to dress.""")
               ),
               ))
    es.add(Cum(EventsCum.MF_CUM_ON_GROIN, "Snowfall on the Bushes",
               subdom_change=1,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=5,
               preg_chance_2=PREGNANCY_CHANCE * 0.01,
               animation_left=DISMISSAL, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Watch her clean herself"),
               desc=ComposedDesc(f"""
                   You stops yourself mere inches from {THEM}'s groin before you release, coating her hips and holes with a thick layer of white. 
                   \\n\\n
                   Your can feel his warmth #sub on#! you.""",
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   \\n\\n"Pardon me, {THEM_FULL_REGNAL}!", you say while quickly cleaning her up.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                   \\n\\n"This was fun", you says as you run your hand across {THEM} shapes before dressing.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   \\n\\n"Let's do more next time", you says as you #S hungrily#! #dom smack her on the ass#!. 
                   """),

                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                    You wanted more, but at least you #S #dom marked#!#! what's yours."""),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                    How #italic could#! you make such a mess on her body?"""),
                                 ),
               ))
    es.add(Cum(EventsCum.MF_CREAMPIE_REGULAR, "Plowing the Fields",
               subdom_change=3,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=20,
               preg_chance_2=PREGNANCY_CHANCE,
               animation_left=WORRY, animation_right=PERSONALITY_BOLD,
               terminal_option=Option(None, OptionCategory.OTHER, "Admire the view"),
               desc=ComposedDesc(f"""
                   "Ugh," you grunt as as you plunge to the hilt, your rod wildly throbbing inside her.
                    You look down just in time to see a white contour remain on her lips as your load overflows out of her around your rod, dripping down her thighs.""",

                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                    "I-I don't know what came over me!" you say, feeling deeply ashamed while avoiding her gaze. \\n\\n
                                     """),
                                 TriggeredDesc(
                                     f" {NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }} \n  {NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}", """
                   With a #dom smack on her ass#!, "Let's do this again sometime.", before finally pulling out. \\n\\n
                   """),
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", """
                   With a #dom smack on her ass#!, "Let's do this again sometime.", before finally pulling out. \\n\\n
                   """),

                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                    "Y-you can do it again if you want", {THEM} says. Judging by the look on her face she #bold wants#!#! you to do it #dom again#!. \\n                 
                   
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                   "What are you doing?!" {THEM} says, shocked at your brazen behaviour. This may not have been #italic quite#! what she was expecting...
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Is the #dom privilege#! of experiencing my body not enough?!" {THEM} says "How #dom dare#! you release inside me
                    like in some #italic random wench?!#!"""),

                                 """\\n\\nShe's left standing as your seed #sub seeps#! out of her slit, her body seeming #italic pleased#! at the warmth within. \\n\\n""",
                                 ),
               ))
    es.add(Cum(EventsCum.MF_CREAMPIE_ON_TOP, "Cherry on Top",
               subdom_change=3,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_sub_chance=30,
               preg_chance_2=PREGNANCY_CHANCE,
               animation_left=SHOCK, animation_right=FLIRTATION_LEFT,
               terminal_option=Option(None, OptionCategory.OTHER, "Wipe the silky threads hanging from your slit"),
               desc=ComposedDesc(f"""
                   You grunt when {THEM}'s slit fully swallows your rod as your muscles lock up with each surge of warmth you unload in her.
                   \\n\\n 
                   """,
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "When did you get so #dom rough #!?!", you say with a #italic shocked #! expression while still pinned below her,
                    your attempts at wriggling out only seeming to please her further.\\n\\n
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                   "What are you doing, {THEM}?!", you say completely stunned by her sudden forcefulness.
                   """),
                                 TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Whatever you need, {THEM_FULL_REGNAL}!", you say while #dom submitting# to being milked into her tight womb\\n\\n
                   """),
                                 f"""{THEM} slowly gets up, white threads hanging from her slit as drops splash onto the ground. """,
                                 TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", f"""
                   You look into her eyes, knowing you couldn't have stopped her from #dom taking#! your seed no matter how hard you tried to resist - and you #sub didn't#!."""),
                                 TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }}", f"""
                   You were pondering leaving her a gift anyway, but to have it #S taken#! from you? Unthinkable!.""")
                                 ),
               ))
    es.add(Cum(EventsCum.MF_CREAMPIE_BREED, "Something to Remember You By",
               subdom_change=-6,
               root_gender=MALE, partner_gender=FEMALE,
               root_become_more_dom_chance=45,
               preg_chance_2=PREGNANCY_CHANCE * 1.5,
               animation_left=PERSONALITY_BOLD, animation_right=WORRY,
               terminal_option=Option(None, OptionCategory.OTHER,
                                      "Feel his seed trickle from your slit for the rest of the day"),
               desc=ComposedDesc(
                   f"""
                    You grunt loudly, a wave of utter relief passing through your whole being as you unload in her, pushing your seed further in
                     with each deep thrust - you feel a #bold warmth#! coat your rod as you lie there, loins deep inside {THEM}.
                   \\n\\n
                    """,
                   """She lies there panting, a white sliver dripping from her #dom conquered#! slit as your seed #italic trickles#! from her womb.""",

                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_SUB}", """
                   You're uncertain what came over you as you take in that you tried to #S mate with her#!.
                    If she wanted your seed she would've #sub taken#! it, not have you #dom force# it in! \\n"""),
                   TriggeredDesc(f"{NOT} = {{ {HAS_TRAIT} = {LIDA_DOM} }} \n {NOT} = {{ {HAS_TRAIT} = {LIDA_SUB} }}",
                                 f"""
                   For a moment your mind wanders to ponder the possible consequences, but the #S bliss#! clears out any such thoughts."""),
                   TriggeredDesc(f"{HAS_TRAIT} = {LIDA_DOM}", f"""
                   "You're #sub mine#! now, {THEM}", you whisper in her ear before finally beginning to pull out. You thrust in to the hilt one last time,
                    a sharp moan escaping her lips as you soak in the warmth of her #dom dominated#! body."""),

                   """\\n\\n""",

                   TriggeredDesc(f"{SCOPE}:{SUBDOM} >= 10", f"""
                   "Use me any way you wish, my {ME_LADY_LORD}!", {THEM} blurts out while dizzily panting.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} > -10 \n{SCOPE}:{SUBDOM} < 10", f"""
                   "What have you done, {ME_NAME}?!", she says in absolute awe at you brazenness.
                   """),
                   TriggeredDesc(f"{SCOPE}:{SUBDOM} <= -10", f"""
                   "Leave, #dom fool#!" {THEM} say #warning furiously#! while kicking you away from her slit.
                   """),

               ),
               ))


# TODO add chance of acquiring fetishes
def define_cum_events(es: EventMap):
    define_cum_events_fm(es)
    define_cum_events_mf(es)


def define_first_events(es: EventMap):
    source_sex_events = get_source_sex_events(es)
    es.add(First(EventsFirst.FM_MEETING_WITH_SPOUSE, "Spicing it Up",
                 source_sex_events=source_sex_events, background="bedchamber",
                 desc=f"""
                 You light some candles and sprinkle some scented petals in your bedchamber,
                 making it an even more inviting den of intimacy. As before, you left
                 a cryptic message inviting {THEM}.
                 \\n\\n
                 He arrives promptly, clearly excited with your spontaneous trysts, and only
                 gives a brief greeting before climbing into bed with you."""))
    es.add(First(EventsFirst.FM_MEETING_WITH_SPOUSE_INITIAL, "Flowers in Bloom",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_VASSAL, "Chains of Command",
                 source_sex_events=source_sex_events, background="study",
                 desc=f"""
                 You send a summons to {THEM} about helping you with interpreting some passages in your study.
                 By now, that's tacitly understood as an invitation to a tryst, which he gladly accepts.
                 Almost immediately, he shows up in your study.
                 """))
    es.add(First(EventsFirst.FM_MEETING_WITH_VASSAL_INITIAL, "Privileges of Power",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_LIEGE, "Mead in my Room?",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_LIEGE_INITIAL, "An Intimate Discussion",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_PRISONER, "Taste of Heaven in Hell",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_PRISONER_INITIAL, "The Sweetest Torture",
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
    es.add(First(EventsFirst.FM_MEETING_WITH_ACQUAINTANCE, "Who Owns Who",
                 source_sex_events=source_sex_events, background="sitting_room",
                 desc=f"""
                 Communicating via your servants, you inform {THEM} that you'd like to get to know them better
                 in your sitting room. Wise to your intentions, he wastes no time arriving, noting the lack of 
                 servants and guards to confirm his guess.
                 \\n\\n
                 You lock eyes, and without exchanging any words do all the communication with your bodies."""))
    es.add(First(EventsFirst.FM_MEETING_WITH_ACQUAINTANCE_INITIAL, "A Chance Encounter",
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
    # MF
    # TODO convert these to the male perspective and offer different meeting events
    es.add(First(EventsFirst.MF_MEETING_WITH_SPOUSE, "Spicing it Up",
                 source_sex_events=source_sex_events, background="bedchamber",
                 root_gender=MALE, partner_gender=FEMALE,
                 desc=f"""
                 You light some candles and sprinkle some scented petals in your bedchamber,
                 making it an even more inviting den of intimacy. As before, you left
                 a cryptic message inviting {THEM}.
                 \\n\\n
                 He arrives promptly, clearly excited with your spontaneous trysts, and only
                 gives a brief greeting before climbing into bed with you."""))
    es.add(First(EventsFirst.MF_MEETING_WITH_SPOUSE_INITIAL, "Flowers in Bloom",
                 source_sex_events=source_sex_events, background="garden",
                 root_gender=MALE, partner_gender=FEMALE,
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
    es.add(First(EventsFirst.MF_MEETING_WITH_VASSAL, "Chains of Command",
                 source_sex_events=source_sex_events, background="study",
                 root_gender=MALE, partner_gender=FEMALE,
                 desc=f"""
                 You send a summons to {THEM} about helping you with interpreting some passages in your study.
                 By now, that's tacitly understood as an invitation to a tryst, which he gladly accepts.
                 Almost immediately, he shows up in your study.
                 """))
    es.add(First(EventsFirst.MF_MEETING_WITH_VASSAL_INITIAL, "Privileges of Power",
                 source_sex_events=source_sex_events, background="study",
                 root_gender=MALE, partner_gender=FEMALE,
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
    es.add(First(EventsFirst.MF_MEETING_WITH_LIEGE, "Mead in my Room?",
                 source_sex_events=source_sex_events, background="bedchamber",
                 root_gender=MALE, partner_gender=FEMALE,
                 desc=f"""
                 It's another long council meeting, and {THEM}'s councillors start streaming out of the
                 room. You, however, remain in the room and say, "My Lord, I have some more council
                 business to discuss with you."
                 \\n\\n
                 Nodding, he responds, "Very good, I appreciate your enthusiasm and hard work."
                 Taking a pause, "But it's getting late, so let us retire to my bedchambers where
                 we can discuss it in more comfort."
                 """))
    es.add(First(EventsFirst.MF_MEETING_WITH_LIEGE_INITIAL, "An Intimate Discussion",
                 source_sex_events=source_sex_events, background="council_chamber",
                 root_gender=MALE, partner_gender=FEMALE,
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
    es.add(First(EventsFirst.MF_MEETING_WITH_PRISONER, "Taste of Heaven in Hell",
                 source_sex_events=source_sex_events, background="dungeon",
                 root_gender=MALE, partner_gender=FEMALE,
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
    es.add(First(EventsFirst.MF_MEETING_WITH_PRISONER_INITIAL, "The Sweetest Torture",
                 source_sex_events=source_sex_events, background="dungeon",
                 root_gender=MALE, partner_gender=FEMALE,
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
    es.add(First(EventsFirst.MF_MEETING_WITH_ACQUAINTANCE, "Who Owns Who",
                 source_sex_events=source_sex_events, background="sitting_room",
                 root_gender=MALE, partner_gender=FEMALE,
                 desc=f"""
                 Communicating via your servants, you inform {THEM} that you'd like to get to know them better
                 in your sitting room. Wise to your intentions, he wastes no time arriving, noting the lack of 
                 servants and guards to confirm his guess.
                 \\n\\n
                 You lock eyes, and without exchanging any words do all the communication with your bodies."""))
    es.add(First(EventsFirst.MF_MEETING_WITH_ACQUAINTANCE_INITIAL, "A Chance Encounter",
                 source_sex_events=source_sex_events, background="courtyard",
                 root_gender=MALE, partner_gender=FEMALE,
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


def main():
    parser = argparse.ArgumentParser(
        description='Generate CK3 Dynamic Affairs events and localization',
    )
    parser.add_argument('-d', '--dry', action='store_true',
                        help="dry run printing the generated strings without exporting to file")
    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
