"""Four-neighbour BFS; coordinates are (row, column)."""

from collections import deque

import numpy as np

from . import FLOOR


def check_grid(grid):
    if grid.ndim != 2 or grid.size == 0 or not np.isin(grid, [0, 1]).all():
        raise ValueError("expected a nonempty 2D binary grid")


def pick_start(grid):
    check_grid(grid)
    cells = np.argwhere(grid == FLOOR)
    return tuple(map(int, cells[0])) if len(cells) else None


def reachable(grid, start):
    check_grid(grid)
    h, w = grid.shape
    dist = np.full((h, w), -1, dtype=np.int32)
    valid = start is not None and 0 <= start[0] < h and 0 <= start[1] < w and grid[start] == FLOOR
    q = deque([start] if valid else [])
    if valid:
        dist[start] = 0
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and grid[ny, nx] == FLOOR and dist[ny, nx] < 0:
                dist[ny, nx] = dist[y, x] + 1
                q.append((ny, nx))
    floor = int((grid == FLOOR).sum())
    reached = int((dist >= 0).sum())
    far = tuple(map(int, np.unravel_index(dist.argmax(), dist.shape))) if reached else None
    return dist, {
        "floor_cells": floor,
        "reached": reached,
        "reach_ratio": reached / max(1, floor),
        "finish": far,
        "path_len": int(dist.max()),
    }


def is_playable(grid, min_reach=0.6, min_path=20):
    _, m = reachable(grid, pick_start(grid))
    return m["reach_ratio"] >= min_reach and m["path_len"] >= min_path


def components(grid):
    check_grid(grid)
    seen = np.zeros(grid.shape, dtype=bool)
    groups = []
    for y, x in np.argwhere(grid == FLOOR):
        if seen[y, x]:
            continue
        queue = deque([(int(y), int(x))])
        seen[y, x] = True
        cells = []
        while queue:
            cy, cx = queue.popleft()
            cells.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1] and grid[ny, nx] == FLOOR and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        groups.append(cells)
    return groups


def shortest_path(dist, finish):
    if finish is None or dist[finish] < 0:
        return []
    path = [finish]
    while dist[path[-1]] > 0:
        y, x = path[-1]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < dist.shape[0] and 0 <= nx < dist.shape[1] and dist[ny, nx] == dist[y, x] - 1:
                path.append((ny, nx))
                break
    return path[::-1]
