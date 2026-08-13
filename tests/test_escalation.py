"""Elapsed BUSINESS time on a ticket (commandcenter/escalation.py).

The desk works 09:00–17:00 Monday to Friday, UTC. Every case here is one an overnight or a weekend gets
wrong: counting wall-clock time makes Monday's queue a wall of breaches nobody can act on, which is worse
than no escalation at all because the team stops looking at the colour.
"""
import pytest

from commandcenter.escalation import business_minutes_between, is_breached

# 2026-08-10 is a Monday; 2026-08-14 a Friday; 2026-08-15/16 the weekend.
MON, TUE, WED, THU, FRI = "2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14"
SAT, SUN, NEXT_MON = "2026-08-15", "2026-08-16", "2026-08-17"


def test_within_one_working_day():
    assert business_minutes_between(f"{MON}T09:00:00Z", f"{MON}T11:30:00Z") == 150


def test_the_clock_does_not_start_before_the_desk_opens():
    """Raised at 07:00, so the first hour of the count is 09:00–10:00, not 07:00–10:00."""
    assert business_minutes_between(f"{MON}T07:00:00Z", f"{MON}T10:00:00Z") == 60


def test_the_clock_stops_when_the_desk_closes():
    assert business_minutes_between(f"{MON}T16:00:00Z", f"{MON}T23:00:00Z") == 60


def test_the_night_in_between_does_not_count():
    """16:30 Monday to 09:30 Tuesday is 17 wall-clock hours and one business hour."""
    assert business_minutes_between(f"{MON}T16:30:00Z", f"{TUE}T09:30:00Z") == 60


def test_a_full_working_day_is_eight_hours():
    assert business_minutes_between(f"{MON}T09:00:00Z", f"{MON}T17:00:00Z") == 480


def test_two_full_days_are_sixteen_hours():
    assert business_minutes_between(f"{MON}T09:00:00Z", f"{TUE}T17:00:00Z") == 960


def test_the_weekend_does_not_count_at_all():
    """The case that floods Monday's queue: Friday afternoon to Monday morning is ONE hour."""
    assert business_minutes_between(f"{FRI}T16:30:00Z", f"{NEXT_MON}T09:30:00Z") == 60


def test_an_interval_entirely_inside_the_weekend_is_zero():
    assert business_minutes_between(f"{SAT}T09:00:00Z", f"{SUN}T17:00:00Z") == 0


def test_an_interval_entirely_overnight_is_zero():
    assert business_minutes_between(f"{MON}T18:00:00Z", f"{TUE}T07:00:00Z") == 0


def test_a_whole_working_week():
    """Monday 09:00 to Friday 17:00 is five eight-hour days."""
    assert business_minutes_between(f"{MON}T09:00:00Z", f"{FRI}T17:00:00Z") == 5 * 480


def test_a_week_spanning_the_weekend_counts_only_the_weekdays():
    assert business_minutes_between(f"{THU}T09:00:00Z", f"{NEXT_MON}T17:00:00Z") == 3 * 480


def test_the_same_instant_is_no_time_at_all():
    assert business_minutes_between(f"{WED}T10:00:00Z", f"{WED}T10:00:00Z") == 0


def test_a_breach_is_measured_on_the_working_clock():
    """A 4-hour SLA raised Friday 16:30 has NOT breached by Monday 09:30 — one business hour has passed."""
    assert is_breached(f"{FRI}T16:30:00Z", f"{NEXT_MON}T09:30:00Z", 240) is False
    assert is_breached(f"{FRI}T16:30:00Z", f"{NEXT_MON}T13:00:00Z", 240) is True


def test_an_end_before_the_start_is_refused():
    """Silently returning zero parks a breaching ticket at the bottom of the queue."""
    with pytest.raises(ValueError):
        business_minutes_between(f"{TUE}T10:00:00Z", f"{MON}T10:00:00Z")


def test_a_missing_timestamp_is_refused():
    with pytest.raises(ValueError):
        business_minutes_between("", f"{MON}T10:00:00Z")
