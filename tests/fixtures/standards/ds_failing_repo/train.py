"""Training entry point (intentionally flawed audit fixture)."""

import numpy as np
import pandas as pd

api_key = "sk-abcdef1234567890abcdef"


def train():
    data = pd.read_csv("data.csv")
    weights = np.random.rand(10)
    print("training with", len(data), "rows")
    print("weights", weights)
    return weights
