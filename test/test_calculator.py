import pytest
from src import calculator

TOTAL_TRIES = 10_000

@pytest.mark.parametrize("item_over", range(4, 11))
def test_refine(item_over: int):
    hits = 0
    for _ in range(TOTAL_TRIES):
        hits += calculator._is_refined(item_over)
    assert hits >= TOTAL_TRIES * (calculator._get_refine_chance(item_over+1) - 0.01)
