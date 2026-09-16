"""Pre-registered paired statistics with no third-party dependency."""

from __future__ import annotations

import math
import random
from statistics import NormalDist


def _bootstrap_means(differences: list[float], n_resamples: int) -> list[float]:
    """Mean of each resample, drawn with a fixed seed so runs are reproducible."""
    rng = random.Random(0)
    size = len(differences)
    return [sum(rng.choices(differences, k=size)) / size for _ in range(n_resamples)]


def paired_bootstrap_ci(a: list[float], b: list[float], n_resamples: int = 10_000,
                        alpha: float = 0.05) -> tuple[float, float, float]:
    if len(a) != len(b) or not a:
        raise ValueError("paired bootstrap requires equally sized non-empty samples")
    differences = [x - y for x, y in zip(a, b)]
    diff = sum(differences) / len(differences)
    samples = sorted(_bootstrap_means(differences, n_resamples))
    low = samples[max(0, math.floor((alpha / 2) * n_resamples))]
    high = samples[min(n_resamples - 1, math.ceil((1 - alpha / 2) * n_resamples) - 1)]
    return diff, low, high


def paired_bootstrap_p_value(a: list[float], b: list[float], n_resamples: int = 2_000) -> float:
    """Two-sided p-value of the paired mean difference under H0: diff = 0.

    Proportion of resampled means under H0 (centered differences) at least as
    extreme as the observed mean difference. Deterministic (fixed seed) and
    bounded below by ``1 / n_resamples`` so a difference observed in every
    resample still reports a finite p-value instead of a misleading exact zero.
    """
    if len(a) != len(b) or not a:
        raise ValueError("paired bootstrap requires equally sized non-empty samples")
    differences = [x - y for x, y in zip(a, b)]
    mean_diff = sum(differences) / len(differences)
    observed = abs(mean_diff)
    if observed == 0.0:
        return 1.0
    centered = [d - mean_diff for d in differences]
    extremes = sum(1 for mean in _bootstrap_means(centered, n_resamples) if abs(mean) >= observed)
    return max(1.0 / n_resamples, extremes / n_resamples)


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
