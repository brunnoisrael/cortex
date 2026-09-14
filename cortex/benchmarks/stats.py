"""Pre-registered paired statistics with no third-party dependency."""

from __future__ import annotations

import math
import random
from statistics import NormalDist


def paired_bootstrap_ci(a: list[float], b: list[float], n_resamples: int = 10_000,
                        alpha: float = 0.05) -> tuple[float, float, float]:
    if len(a) != len(b) or not a:
        raise ValueError("paired bootstrap requires equally sized non-empty samples")
    differences = [x - y for x, y in zip(a, b)]
    diff = sum(differences) / len(differences)
    rng = random.Random(0)
    samples = [sum(rng.choice(differences) for _ in differences) / len(differences) for _ in range(n_resamples)]
    samples.sort()
    low = samples[max(0, math.floor((alpha / 2) * n_resamples))]
    high = samples[min(n_resamples - 1, math.ceil((1 - alpha / 2) * n_resamples) - 1)]
    return diff, low, high


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    decisions = [False] * len(p_values)
    for rank, index in enumerate(sorted(range(len(p_values)), key=lambda i: p_values[i])):
        if p_values[index] <= alpha / (len(p_values) - rank):
            decisions[index] = True
        else:
            break
    return decisions


def power_analysis(baseline_rate: float, mde: float, power: float = 0.8, alpha: float = 0.05) -> int:
    if not 0 <= baseline_rate <= 1 or mde <= 0 or not 0 < power < 1:
        raise ValueError("invalid proportion power inputs")
    p2 = min(1.0, max(0.0, baseline_rate + mde))
    pooled = (baseline_rate + p2) / 2
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    numerator = (z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
                 z_power * math.sqrt(baseline_rate * (1 - baseline_rate) + p2 * (1 - p2))) ** 2
    return max(1, math.ceil(numerator / (mde ** 2)))
