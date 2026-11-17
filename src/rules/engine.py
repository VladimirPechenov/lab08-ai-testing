"""Deterministic forward chaining with priorities, refraction and audit trail."""

from dataclasses import dataclass, field
from typing import Callable

Fact = tuple


@dataclass
class Rule:
    name: str
    condition: Callable[[set[Fact]], bool]
    action: Callable[[set[Fact]], None]
    priority: int = 0


@dataclass
class Engine:
    rules: list[Rule] = field(default_factory=list)
    facts: set[Fact] = field(default_factory=set)
    log: list[dict] = field(default_factory=list)

    def add(self, rule: Rule) -> None:
        if any(r.name == rule.name for r in self.rules):
            raise ValueError(f"Duplicate rule: {rule.name}")
        self.rules.append(rule)

    def assert_fact(self, *fact) -> None:
        self.facts.add(tuple(fact))

    def retract(self, *fact) -> None:
        self.facts.discard(tuple(fact))

    def run(self, max_cycles: int = 100) -> list[str]:
        """Rebuild agenda after every firing; each instance fires once per tick."""
        fired = []
        considered = set()
        ordered = sorted(self.rules, key=lambda r: (-r.priority, r.name))
        for _ in range(max_cycles):
            for rule in ordered:
                if rule.name in considered or not rule.condition(self.facts):
                    continue
                before = self.facts.copy()
                rule.action(self.facts)
                considered.add(rule.name)
                if self.facts == before:
                    continue
                fired.append(rule.name)
                self.log.append(
                    {
                        "rule": rule.name,
                        "priority": rule.priority,
                        "added": sorted(self.facts - before),
                        "removed": sorted(before - self.facts),
                        "facts": sorted(self.facts),
                    }
                )
                break
            else:
                return fired
        raise RuntimeError("Inference cycle limit exceeded; inspect the rule base")
