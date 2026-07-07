"""Wire the evaluation gate into the test suite."""

from __future__ import annotations

from evaluate import check_gate


def test_gate_passes_above_floor() -> None:
    assert check_gate(0.90) == 0


def test_gate_blocks_below_floor() -> None:
    assert check_gate(0.50) == 1
