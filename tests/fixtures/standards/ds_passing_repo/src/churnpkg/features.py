"""Feature engineering."""

from __future__ import annotations


def add_features(rows: list[int]) -> list[int]:
    """Shift each row value by one to stand in for a feature transform."""

    return [row + 1 for row in rows]
