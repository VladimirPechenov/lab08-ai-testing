"""Бот-плеер: ходит по сетке уровня к финишу (жадно по BFS-дистанции), собирает метрики."""

import random
from dataclasses import dataclass, field

import numpy as np

from aiunder.validator import check_grid


@dataclass
class BotMetrics:
    steps: int = 0
    reached_goal: bool = False
    stuck_events: int = 0
    visited: set = field(default_factory=set)
    path: list = field(default_factory=list)


def run_bot(
    grid: np.ndarray, dist: np.ndarray, start: tuple, goal: tuple, max_steps=2000, epsilon=0.1, seed=0
) -> BotMetrics:
    check_grid(grid)
    if dist.shape != grid.shape or not 0 <= epsilon <= 1 or max_steps < 0:
        raise ValueError("invalid distance shape, epsilon or max_steps")
    for point in (start, goal):
        if not (0 <= point[0] < grid.shape[0] and 0 <= point[1] < grid.shape[1]) or grid[point] != 0:
            raise ValueError("start and goal must be floor cells")
    rng = random.Random(seed)
    pos, m = start, BotMetrics(visited={start}, path=[start], reached_goal=start == goal)
    for _ in range(max_steps):
        if m.reached_goal:
            break
        y, x = pos
        moves = [
            (y + dy, x + dx)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= y + dy < grid.shape[0]
            and 0 <= x + dx < grid.shape[1]
            and grid[y + dy, x + dx] == 0
            and dist[y + dy, x + dx] >= 0
        ]
        if not moves:
            m.stuck_events += 1
            break
        # dist считается ОТ финиша: идём в клетку с меньшим значением; иногда случайно (epsilon)
        nxt = rng.choice(moves) if rng.random() < epsilon else min(moves, key=lambda p: dist[p])
        if dist[nxt] >= dist[pos]:
            m.stuck_events += 1
        pos = nxt
        m.steps += 1
        m.visited.add(pos)
        m.path.append(pos)
        m.reached_goal = pos == goal
    return m
