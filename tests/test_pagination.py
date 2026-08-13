"""Paging the audit export (commandcenter/pagination.py).

The property under test is the one the compliance export depends on: every row appears EXACTLY ONCE across
the pages. The cases that matter are the ones with TIED timestamps, because audit rows are written in
batches and a batch shares a timestamp to the second — which is exactly where offset paging silently drops
some rows and repeats others.
"""
import pytest

from commandcenter.pagination import export_all, export_is_complete, page

# Ten rows, all written in the same second — one whole page boundary inside a single tied group.
TIED = [{"id": f"a{i:02d}", "created_at": "2026-08-12T10:00:00Z"} for i in range(10)]

MIXED = [
    {"id": "r1", "created_at": "2026-08-12T09:00:00Z"},
    {"id": "r2", "created_at": "2026-08-12T10:00:00Z"},
    {"id": "r3", "created_at": "2026-08-12T10:00:00Z"},
    {"id": "r4", "created_at": "2026-08-12T10:00:00Z"},
    {"id": "r5", "created_at": "2026-08-12T11:00:00Z"},
]


def test_the_first_page_is_the_first_rows_in_order():
    got = page(MIXED, limit=2)
    assert [r["id"] for r in got] == ["r1", "r2"]


def test_the_next_page_resumes_after_the_cursor_row():
    first = page(MIXED, limit=2)
    second = page(MIXED, after=first[-1], limit=2)
    assert [r["id"] for r in second] == ["r3", "r4"]


def test_a_page_boundary_inside_a_tied_group_does_not_drop_the_rest_of_it():
    """The bug this module exists for: r3 and r4 share r2's timestamp and must still be returned."""
    first = page(MIXED, limit=2)          # ends on r2, mid-tie
    rest = page(MIXED, after=first[-1], limit=100)
    assert [r["id"] for r in rest] == ["r3", "r4", "r5"]


def test_paging_all_the_way_through_returns_every_row_exactly_once():
    out = export_all(MIXED, limit=2)
    assert [r["id"] for r in out] == ["r1", "r2", "r3", "r4", "r5"]
    assert export_is_complete(MIXED, out)


def test_an_entirely_tied_batch_pages_completely():
    """Ten rows in one second, two at a time. Offset paging loses some of these."""
    out = export_all(TIED, limit=2)
    assert len(out) == 10
    assert sorted(r["id"] for r in out) == sorted(r["id"] for r in TIED)
    assert export_is_complete(TIED, out)


def test_no_row_is_returned_twice():
    out = export_all(TIED, limit=3)
    ids = [r["id"] for r in out]
    assert len(ids) == len(set(ids)), f"duplicated rows: {ids}"


def test_every_page_size_gives_the_same_export():
    """A correct pager does not depend on where the boundaries happen to fall."""
    reference = export_all(MIXED, limit=1)
    for size in (2, 3, 4, 5, 100):
        assert export_all(MIXED, limit=size) == reference


def test_the_last_page_is_empty_so_the_loop_terminates():
    last = page(MIXED, after={"id": "r5", "created_at": "2026-08-12T11:00:00Z"}, limit=10)
    assert last == []


def test_an_empty_table_exports_nothing():
    assert export_all([], limit=10) == []


def test_a_page_larger_than_the_table_returns_the_table():
    assert len(page(MIXED, limit=1000)) == 5


def test_a_non_positive_limit_is_refused():
    """A limit of zero returns an empty page forever — the caller's loop stops with a partial export."""
    with pytest.raises(ValueError):
        page(MIXED, limit=0)
    with pytest.raises(ValueError):
        page(MIXED, limit=-1)
