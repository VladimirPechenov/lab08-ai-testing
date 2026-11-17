import pytest

from aiunder.fsm import GuardFSM, State
from rules.guard_rules import build


@pytest.mark.parametrize(
    "source,trigger,target",
    [
        (State.PATROL, "see_player", State.ALERT),
        (State.PATROL, "hear_noise", State.ALERT),
        (State.ALERT, "confirm", State.CHASE),
        (State.ALERT, "lost", State.SEARCH),
        (State.CHASE, "in_range", State.ATTACK),
        (State.ATTACK, "out_of_range", State.CHASE),
        (State.CHASE, "lost", State.SEARCH),
        (State.SEARCH, "see_player", State.CHASE),
        (State.SEARCH, "timeout", State.PATROL),
    ],
)
def test_transition(source, trigger, target):
    g = GuardFSM()
    g.state = source
    assert g.fire(trigger)
    assert g.state == target
    assert g.history == [(source, trigger, target)]


def test_invalid_event_preserves_state_and_history():
    g = GuardFSM()
    assert not g.fire("teleport")
    assert g.state == State.PATROL and g.history == []


def test_search_timeout_boundary():
    g = GuardFSM()
    g.state = State.SEARCH
    g.tick(2.99)
    assert g.state == State.SEARCH
    g.tick(0.01)
    assert g.state == State.PATROL


def test_visible_target_has_priority_over_timeout():
    g = GuardFSM()
    g.state = State.SEARCH
    g.tick(4, visible=True)
    assert g.state == State.CHASE


def test_repeated_search_resets_timer():
    g = GuardFSM()
    g.state = State.SEARCH
    g.tick(2)
    g.fire("see_player")
    g.fire("lost")
    g.tick(2)
    assert g.state == State.SEARCH and g.elapsed == 2


def test_negative_dt_rejected():
    with pytest.raises(ValueError):
        GuardFSM().tick(-1)


def test_darkness_hides_player():
    e = build(("g1",))
    e.assert_fact("at", "g1", "room")
    e.assert_fact("at", "player", "room")
    e.run()
    assert ("hidden", "g1", "player") in e.facts
    assert ("sees", "g1", "player") not in e.facts


def test_light_exposes_player_and_raises_alarm():
    e = build(("g1", "g2"))
    for who in ("g1", "player"):
        e.assert_fact("at", who, "room")
    e.assert_fact("light_on", "room")
    e.run()
    assert ("state", "g1", "chase") in e.facts
    assert ("state", "g2", "search") in e.facts
    assert ("alarm",) in e.facts


def test_sight_overrides_noise():
    e = build(("g1",))
    e.assert_fact("sees", "g1", "player")
    e.assert_fact("hears", "g1", "noise")
    fired = e.run()
    assert ("state", "g1", "chase") in e.facts
    assert "hear_noise_g1" not in fired
