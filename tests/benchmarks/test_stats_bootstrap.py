from cortex.benchmarks.stats import (
    holm_bonferroni,
    paired_bootstrap_ci,
    paired_bootstrap_p_value,
    power_analysis,
)


def test_paired_stats_are_deterministic():
    first = paired_bootstrap_ci([1, 1, 0], [0, 0, 0], n_resamples=100)
    assert first == paired_bootstrap_ci([1, 1, 0], [0, 0, 0], n_resamples=100)
    assert holm_bonferroni([0.001, 0.9]) == [True, False]
    assert power_analysis(0.5, 0.1) > 0


def test_paired_bootstrap_p_value_detects_significant_differences():
    # Large consistent advantage must yield a small p-value bounded below by 1/n_resamples
    p_sig = paired_bootstrap_p_value([1.0] * 20, [0.0] * 20, n_resamples=1000)
    assert p_sig <= 0.05
    assert p_sig == 1.0 / 1000

    # Identical samples must return p-value of 1.0
    assert paired_bootstrap_p_value([0.5] * 10, [0.5] * 10, n_resamples=500) == 1.0

