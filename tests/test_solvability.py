import numpy as np
import pytest

from aiunder import bsp
from aiunder.validator import is_playable, pick_start, reachable
from bot.player_bot import run_bot


@pytest.mark.timeout(5)
@pytest.mark.parametrize("seed", range(100))
def test_level_is_playable(seed):
    grid = bsp.generate(seed=seed)
    start = pick_start(grid)
    _, metrics = reachable(grid, start)
    assert metrics["reach_ratio"] == 1.0
    assert is_playable(grid)
    goal = metrics["finish"]
    dist, _ = reachable(grid, goal)
    bot = run_bot(grid, dist, start, goal, epsilon=0, max_steps=metrics["path_len"], seed=seed)
    assert bot.reached_goal
    assert bot.steps == metrics["path_len"]
    assert all(grid[p] == 0 for p in bot.path)
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(bot.path, bot.path[1:], strict=False))
    assert np.array_equal(grid, bsp.generate(seed=seed))
