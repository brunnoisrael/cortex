from cortex.benchmarks.stats import holm_bonferroni, paired_bootstrap_ci, power_analysis


def test_paired_stats_are_deterministic():
    first = paired_bootstrap_ci([1, 1, 0], [0, 0, 0], n_resamples=100)
    assert first == paired_bootstrap_ci([1, 1, 0], [0, 0, 0], n_resamples=100)
    assert holm_bonferroni([0.001, 0.9]) == [True, False]
    assert power_analysis(0.5, 0.1) > 0
