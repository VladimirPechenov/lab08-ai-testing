import numpy as np
import pytest

from aiunder.validator import reachable
from bot.player_bot import run_bot


def test_unreachable_goal_records_stuck():
    grid = np.array([[0, 1, 0]])
    dist, _ = reachable(grid, (0, 2))
    m = run_bot(grid, dist, (0, 0), (0, 2))
    assert not m.reached_goal and m.stuck_events == 1 and m.steps == 0


def test_wall_is_never_a_move_even_with_stale_distance():
    m = run_bot(np.array([[0, 1, 0]]), np.array([[2, 1, 0]]), (0, 0), (0, 2))
    assert not m.reached_goal and m.path == [(0, 0)]


def test_seed_reproduces_random_walk():
    grid = np.zeros((5, 5), dtype=np.int8)
    dist, _ = reachable(grid, (4, 4))
    assert run_bot(grid, dist, (0, 0), (4, 4), epsilon=1, seed=7) == run_bot(
        grid, dist, (0, 0), (4, 4), epsilon=1, seed=7
    )


@pytest.mark.parametrize("epsilon", [-0.1, 1.1])
def test_invalid_epsilon(epsilon):
    with pytest.raises(ValueError):
        run_bot(np.zeros((1, 2)), np.array([[1, 0]]), (0, 0), (0, 1), epsilon=epsilon)
