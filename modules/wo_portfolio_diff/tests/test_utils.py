import wo_portfolio_diff.utils as unit

def test_increment():
    n = 1
    result = unit.increment(n)
    assert result == n + 1
