"""Splitting a refund across order lines (commandcenter/refunds.py).

The property under test is the one Finance reconciles against: THE PARTS SUM TO THE WHOLE, exactly, for
every input. Most of these cases are chosen because rounding each share independently gets them wrong —
some by losing a cent, some by inventing one, and both are reconciliation breaks somebody chases by hand.
"""
import pytest

from commandcenter.refunds import refund_is_balanced, split_refund


def test_a_refund_that_divides_evenly():
    assert split_refund(3000, [1000, 1000, 1000]) == [1000, 1000, 1000]


def test_a_refund_that_does_not_divide_evenly_still_sums_to_the_whole():
    """10000 across three equal lines is 3333.33… each. Independent rounding loses a cent."""
    out = split_refund(10000, [1000, 1000, 1000])
    assert sum(out) == 10000
    assert out == [3334, 3333, 3333]


def test_the_leftover_cents_go_to_the_largest_discarded_fraction():
    """Lines 1 and 2 give up more of a cent than line 3, so they get the two spare cents."""
    out = split_refund(1000, [333, 333, 334])
    assert sum(out) == 1000
    assert out == [333, 333, 334]


def test_a_refund_is_proportional_to_the_line_values():
    out = split_refund(10000, [5000, 3000, 2000])
    assert out == [5000, 3000, 2000]
    assert sum(out) == 10000


def test_a_single_line_takes_the_whole_refund():
    assert split_refund(4999, [1234]) == [4999]


def test_a_penny_refund_across_many_lines_still_balances():
    """The extreme case: one cent, five lines. Exactly one line may have it."""
    out = split_refund(1, [100, 100, 100, 100, 100])
    assert sum(out) == 1
    assert sorted(out) == [0, 0, 0, 0, 1]


def test_a_zero_refund_allocates_nothing_to_anybody():
    assert split_refund(0, [100, 200]) == [0, 0]


def test_a_fully_comped_order_spreads_evenly_rather_than_dividing_by_zero():
    out = split_refund(10, [0, 0, 0])
    assert sum(out) == 10
    assert out == [4, 3, 3]


def test_the_same_order_splits_the_same_way_twice():
    """Finance re-runs these. A tie broken differently on the second run is a break."""
    args = (7777, [1111, 1111, 1111, 1111, 1111, 1111, 1111])
    assert split_refund(*args) == split_refund(*args)


def test_every_allocation_is_a_whole_non_negative_number_of_cents():
    out = split_refund(9999, [1, 2, 3, 4, 5000])
    assert all(isinstance(c, int) and c >= 0 for c in out)
    assert sum(out) == 9999


def test_it_balances_across_a_spread_of_awkward_totals():
    lines = [700, 1300, 2000, 33]
    for total in (1, 2, 3, 99, 101, 4999, 10000, 123457):
        out = split_refund(total, lines)
        assert sum(out) == total, f"{total} did not balance: {out}"
        assert refund_is_balanced(total, out)


def test_a_negative_refund_is_refused():
    with pytest.raises(ValueError):
        split_refund(-1, [100])


def test_a_negative_line_is_refused():
    with pytest.raises(ValueError):
        split_refund(100, [100, -1])


def test_no_lines_at_all_is_refused():
    with pytest.raises(ValueError):
        split_refund(100, [])
