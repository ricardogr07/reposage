"""Evaluation gate: fail the build when AUC drops below its floor."""

from __future__ import annotations

import sys

AUC_FLOOR = 0.75


def check_gate(auc: float) -> int:
    """Return 0 when auc clears the floor, else 1."""

    if auc >= AUC_FLOOR:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(check_gate(0.82))
