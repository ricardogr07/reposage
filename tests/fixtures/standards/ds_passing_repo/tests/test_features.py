"""Behavioral test for feature engineering."""

from __future__ import annotations

import pytest

from churnpkg.features import add_features


def test_add_features_shifts_values() -> None:
    assert add_features([1, 2]) == pytest.approx([2, 3])
