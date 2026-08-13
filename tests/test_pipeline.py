"""Pipeline-rollup tests (cc-code-1).

`test_pipeline_total_counts_each_deal_once` is the REPRODUCTION TARGET: a multi-currency deal that arrives as
several JOIN rows must contribute its converted value ONCE. It fails on the shipped code (the deal is
double-counted) and passes once the rollup dedups by deal id. Isolated to this bug — no other scenario shares it.
"""
from commandcenter import pipeline

# ACME is ONE $100k deal that settles in USD + EUR → it arrives as TWO rows, each with the full $100k.
_ROWS = [
    {"id": "D1", "name": "Acme",     "amount_usd": 100000, "currency": "USD", "stage": "proposal"},
    {"id": "D1", "name": "Acme",     "amount_usd": 100000, "currency": "EUR", "stage": "proposal"},
    {"id": "D2", "name": "Globex",   "amount_usd": 50000,  "currency": "USD", "stage": "qualified"},
    {"id": "D3", "name": "Won Corp", "amount_usd": 90000,  "currency": "USD", "stage": "closed_won"},  # not open
]


def test_is_open():
    assert pipeline.is_open(_ROWS[0]) is True
    assert pipeline.is_open(_ROWS[3]) is False


def test_single_currency_deal_counted_once():
    assert pipeline.pipeline_total([_ROWS[2]]) == 50000


def test_closed_deals_are_excluded():
    assert pipeline.pipeline_total([_ROWS[3]]) == 0


def test_pipeline_total_counts_each_deal_once():
    # D1 shows up as two currency rows but is ONE $100k deal; total open pipeline is D1 100k + D2 50k = 150k,
    # NOT 250k. The shipped rollup counts D1 twice.
    assert pipeline.pipeline_total(_ROWS) == 150000
