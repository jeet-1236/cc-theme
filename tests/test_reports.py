"""The daily revenue report (commandcenter/reports.py).

The business day is the UTC calendar day. These assertions are deliberately written against timestamps on
BOTH sides of midnight UTC, because a report that follows the reporting server's local clock instead agrees
with this one for most of the day and disagrees only near the boundary — which is exactly why such a defect
reaches production.
"""
from commandcenter.reports import business_day, daily_revenue


def test_a_midday_order_is_reported_on_its_own_day():
    assert business_day("2026-08-12T15:00:00Z") == "2026-08-12"


def test_an_order_just_after_midnight_utc_belongs_to_the_new_day():
    """02:10 UTC on the 12th is the 12th's revenue — on every server, in every region."""
    assert business_day("2026-08-12T02:10:00Z") == "2026-08-12"


def test_an_order_just_before_midnight_utc_belongs_to_the_old_day():
    assert business_day("2026-08-11T23:40:00Z") == "2026-08-11"


def test_the_first_and_last_instant_of_a_day():
    assert business_day("2026-08-12T00:00:00Z") == "2026-08-12"
    assert business_day("2026-08-12T23:59:59Z") == "2026-08-12"


def test_revenue_is_bucketed_by_the_utc_day():
    orders = [
        {"ts": "2026-08-11T23:40:00Z", "amount_cents": 12000},   # the 11th
        {"ts": "2026-08-12T02:10:00Z", "amount_cents": 48000},   # the 12th
        {"ts": "2026-08-12T15:00:00Z", "amount_cents": 30000},   # the 12th
    ]
    assert daily_revenue(orders) == {"2026-08-11": 12000, "2026-08-12": 78000}


def test_a_day_with_no_orders_is_absent_rather_than_zero():
    assert daily_revenue([{"ts": "2026-08-12T15:00:00Z", "amount_cents": 100}]) == {"2026-08-12": 100}


def test_no_orders_is_an_empty_report():
    assert daily_revenue([]) == {}
