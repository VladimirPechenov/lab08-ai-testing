import numpy as np

from bot.player_bot import run_bot


def test_goal_on_last_allowed_move():
    m = run_bot(np.zeros((1, 2), dtype=np.int8), np.array([[1, 0]]), (0, 0), (0, 1), max_steps=1, epsilon=0)
    assert m.reached_goal
    assert m.steps == 1
    assert m.visited == {(0, 0), (0, 1)}


def test_start_at_goal_costs_zero_moves():
    m = run_bot(np.zeros((1, 1), dtype=np.int8), np.array([[0]]), (0, 0), (0, 0), max_steps=0)
    assert m.reached_goal
    assert m.steps == 0
