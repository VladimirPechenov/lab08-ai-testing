"""Reproduce 100 seeds for greedy, epsilon-greedy and random policies."""

import csv
import json
import platform
from pathlib import Path
from statistics import mean

from aiunder import bsp
from aiunder.validator import pick_start, reachable
from bot.player_bot import run_bot


def main():
    out = Path("results")
    out.mkdir(exist_ok=True)
    rows = []
    for seed in range(100):
        grid = bsp.generate(seed=seed)
        start = pick_start(grid)
        _, level = reachable(grid, start)
        goal = level["finish"]
        dist, _ = reachable(grid, goal)
        for policy, epsilon in (("greedy", 0), ("epsilon", 0.1), ("random", 1)):
            m = run_bot(grid, dist, start, goal, epsilon=epsilon, seed=seed, max_steps=2000)
            rows.append(
                dict(
                    seed=seed,
                    policy=policy,
                    epsilon=epsilon,
                    steps=m.steps,
                    reached_goal=m.reached_goal,
                    stuck_events=m.stuck_events,
                    coverage=len(m.visited) / level["floor_cells"],
                    shortest=level["path_len"],
                    reach_ratio=level["reach_ratio"],
                )
            )
    with (out / "bot_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for policy in ("greedy", "epsilon", "random"):
        subset = [r for r in rows if r["policy"] == policy]
        summary[policy] = {
            "successes": sum(r["reached_goal"] for r in subset),
            "levels": len(subset),
            **{k: mean(r[k] for r in subset) for k in ("steps", "stuck_events", "coverage")},
        }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "environment.json").write_text(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "seeds": "0..99",
                "width": 64,
                "height": 48,
                "max_steps": 2000,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
