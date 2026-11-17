"""Small guard FSM; elapsed time advances only in SEARCH."""
from enum import Enum


class State(Enum):
    PATROL = "patrol"
    ALERT = "alert"
    CHASE = "chase"
    ATTACK = "attack"
    SEARCH = "search"


class GuardFSM:
    transitions = {
        (State.PATROL, "see_player"): State.ALERT,
        (State.PATROL, "hear_noise"): State.ALERT,
        (State.ALERT, "confirm"): State.CHASE,
        (State.ALERT, "lost"): State.SEARCH,
        (State.CHASE, "in_range"): State.ATTACK,
        (State.ATTACK, "out_of_range"): State.CHASE,
        (State.CHASE, "lost"): State.SEARCH,
        (State.SEARCH, "see_player"): State.CHASE,
        (State.SEARCH, "timeout"): State.PATROL,
    }

    def __init__(self, search_timeout=3.0):
        if search_timeout <= 0:
            raise ValueError("search_timeout must be positive")
        self.state = State.PATROL
        self.elapsed = 0.0
        self.search_timeout = search_timeout
        self.history = []

    def fire(self, trigger):
        target = self.transitions.get((self.state, trigger))
        if target is None:
            return False
        self.history.append((self.state, trigger, target))
        self.state = target
        self.elapsed = 0.0
        return True

    def tick(self, dt, visible=False):
        if dt < 0:
            raise ValueError("dt must be nonnegative")
        if visible:
            self.fire("see_player")
        elif self.state == State.SEARCH:
            self.elapsed += dt
            if self.elapsed >= self.search_timeout:
                self.fire("timeout")
