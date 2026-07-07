"""Model training with a seeded run and experiment tracking."""

from __future__ import annotations

import random

import mlflow


def train() -> float:
    """Train a stub model deterministically and log its metric."""

    random.seed(42)
    auc = 0.82
    mlflow.log_metric("auc", auc)
    return auc
