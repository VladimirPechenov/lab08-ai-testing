"""Independent generation and NPC tick timing; excludes BFS and rendering."""
import math
import time

from . import bsp
from .fsm import GuardFSM, State

GEN_BUDGET_MS = 50.0
TICK_BUDGET_MS = 1.0


def stats(values):
    ordered = sorted(values)
    return {"mean_ms": sum(values) / len(values), "p95_ms": ordered[math.ceil(.95 * len(values)) - 1],
            "max_ms": max(values), "samples": len(values)}


def measure():
    bsp.generate(seed=1000)
    times = []
    for seed in range(100):
        t = time.perf_counter_ns()
        bsp.generate(seed=seed)
        times.append((time.perf_counter_ns()-t) / 1e6)
    g = GuardFSM()
    ticks = []
    for _ in range(1000):
        g.state = State.SEARCH
        g.elapsed = 0
        t = time.perf_counter_ns()
        g.tick(1/60, visible=True)
        ticks.append((time.perf_counter_ns()-t) / 1e6)
    return {"generation": stats(times), "ai_tick": stats(ticks),
            "budgets_ms": {"generation_p95": GEN_BUDGET_MS, "ai_tick_p95": TICK_BUDGET_MS}}
