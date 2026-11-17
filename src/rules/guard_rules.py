"""Thirteen rule schemas for a stealth scene. Time is in seconds."""

from .engine import Engine, Rule


def has(facts, *pat):
    return tuple(pat) in facts


def value(facts, pred, entity, default=None):
    return next((f[2] for f in facts if f[:2] == (pred, entity)), default)


def now(facts):
    return next((f[1] for f in facts if f[0] == "time"), 0)


def replace(facts, pred, entity, val):
    facts.difference_update({f for f in facts if f[:2] == (pred, entity)})
    facts.add((pred, entity, val))


def set_state(facts, guard, new):
    replace(facts, "state", guard, new)
    replace(facts, "since", guard, now(facts))


def co_located(facts, guard):
    zone = value(facts, "at", guard)
    return zone is not None and zone == value(facts, "at", "player")


def age(facts, guard):
    return now(facts) - value(facts, "since", guard, now(facts))


def build(guards=("g1", "g2")) -> Engine:
    e = Engine()
    e.assert_fact("time", 0)
    for g in guards:
        e.assert_fact("state", g, "patrol")
        e.assert_fact("since", g, 0)

        def add(name, priority, condition, action, g=g):
            e.add(Rule(f"{name}_{g}", lambda f: condition(f, g), lambda f: action(f, g), priority))

        add(
            "dark_zone",
            100,
            lambda f, g: co_located(f, g) and not has(f, "light_on", value(f, "at", g)),
            lambda f, g: f.add(("hidden", g, "player")),
        )
        add(
            "light_visible",
            95,
            lambda f, g: co_located(f, g) and has(f, "light_on", value(f, "at", g)),
            lambda f, g: f.add(("sees", g, "player")),
        )
        add(
            "door_opened",
            90,
            lambda f, g: has(f, "door_opened", value(f, "at", g)),
            lambda f, g: f.add(("hears", g, "noise")),
        )
        add(
            "remember_target",
            85,
            lambda f, g: has(f, "sees", g, "player") and value(f, "at", "player") is not None,
            lambda f, g: replace(f, "last_seen", g, value(f, "at", "player")),
        )
        add(
            "see_player",
            80,
            lambda f, g: has(f, "sees", g, "player") and not has(f, "state", g, "chase"),
            lambda f, g: set_state(f, g, "chase"),
        )
        add(
            "raise_alarm",
            75,
            lambda f, g: has(f, "state", g, "chase") and not has(f, "alarm"),
            lambda f, g: f.add(("alarm",)),
        )
        add(
            "lost_target",
            70,
            lambda f, g: has(f, "state", g, "chase") and not has(f, "sees", g, "player"),
            lambda f, g: set_state(f, g, "search"),
        )
        add(
            "alarm_join",
            65,
            lambda f, g: (
                has(f, "alarm") and value(f, "state", g) in ("patrol", "investigate") and not has(f, "responded", g)
            ),
            lambda f, g: (set_state(f, g, "search"), f.add(("responded", g))),
        )
        add(
            "hear_noise",
            50,
            lambda f, g: has(f, "hears", g, "noise") and has(f, "state", g, "patrol"),
            lambda f, g: set_state(f, g, "investigate"),
        )
        add(
            "light_off",
            45,
            lambda f, g: has(f, "power_failed", value(f, "at", g)) and has(f, "state", g, "patrol"),
            lambda f, g: (set_state(f, g, "investigate"), f.add(("target", g, "switch"))),
        )
        add(
            "search_timeout",
            30,
            lambda f, g: (
                has(f, "state", g, "search")
                and age(f, g) >= 10
                and not has(f, "sees", g, "player")
                and not has(f, "hears", g, "noise")
            ),
            lambda f, g: (set_state(f, g, "patrol"), f.add(("responded", g))),
        )
        add(
            "return_post",
            20,
            lambda f, g: (
                has(f, "state", g, "investigate")
                and age(f, g) >= 5
                and not has(f, "sees", g, "player")
                and not has(f, "hears", g, "noise")
                and not has(f, "power_failed", value(f, "at", g))
            ),
            lambda f, g: (set_state(f, g, "patrol"), f.discard(("target", g, "switch"))),
        )
    e.add(
        Rule(
            "alarm_reset",
            lambda f: has(f, "alarm") and all(has(f, "state", g, "patrol") for g in guards),
            lambda f: f.difference_update({x for x in f if x[0] in ("alarm", "responded")}),
            10,
        )
    )
    return e
