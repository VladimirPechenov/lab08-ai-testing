import json
from pathlib import Path

import pytest

from aiunder.performance import GEN_BUDGET_MS, TICK_BUDGET_MS, measure


@pytest.fixture(scope="module")
def measurements():
    result = measure()
    Path("results").mkdir(exist_ok=True)
    Path("results/performance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


@pytest.mark.timeout(10)
def test_generation_budget(measurements):
    assert measurements["generation"]["p95_ms"] < GEN_BUDGET_MS


@pytest.mark.timeout(10)
def test_ai_tick_budget(measurements):
    assert measurements["ai_tick"]["p95_ms"] < TICK_BUDGET_MS
