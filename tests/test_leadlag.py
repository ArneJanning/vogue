from vogue.analysis import detrend, pearson, cross_correlate, LeadLag


def _bump(center, lo=2000, hi=2020):
    """Triangular bump peaking at `center` (height 10), zero far away."""
    return {y: max(0, 10 - abs(y - center)) for y in range(lo, hi + 1)}


def test_detrend_methods():
    assert detrend([2, 4, 6], "none") == [2, 4, 6]
    assert detrend([0, 5, 10], "peak") == [0.0, 0.5, 1.0]
    assert detrend([1, 2, 3], "diff") == [1, 1]
    z = detrend([1, 2, 3], "zscore")
    assert abs(sum(z)) < 1e-9 and z[0] < 0 < z[2]
    assert detrend([5, 5, 5], "zscore") == [0.0, 0.0, 0.0]  # zero variance


def test_pearson_basic():
    assert abs(pearson([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9
    assert abs(pearson([1, 2, 3], [3, 2, 1]) + 1.0) < 1e-9
    assert pearson([1, 1, 1], [1, 2, 3]) == 0.0  # zero variance -> 0


def test_cross_correlate_recovers_known_lead():
    a = _bump(2010)   # the lagging series (peak 2010)
    b = _bump(2007)   # the leading series (peak 2007) -> leads a by 3 years
    res = cross_correlate(a, b, max_lag=6, method="zscore")
    assert isinstance(res, LeadLag)
    assert res.best_lag == 3            # b leads a by 3
    assert res.best_corr > 0.9
    assert res.method == "zscore"
    assert res.profile[3] >= res.profile[0]


def test_cross_correlate_insufficient_data_returns_none():
    assert cross_correlate({2010: 5}, {2009: 4}, max_lag=6) is None
