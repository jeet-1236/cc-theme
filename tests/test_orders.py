"""Order totals (commandcenter/orders.py).

Every figure below is in cents and is the amount the payment processor settles, so the assertions are exact
equalities — "close enough" is a reconciliation break Finance chases by hand.

The arithmetic is worth writing out once, because it is what the assertions encode:

    subtotal 10000, 10% off, 20% tax   →  discounted 9000, tax 1800, total 10800
"""
from commandcenter.orders import discounted_subtotal, order_total


def test_the_discount_comes_off_the_subtotal():
    assert discounted_subtotal(10000, 10) == 9000
    assert discounted_subtotal(10000, 0) == 10000


def test_a_domestic_order_with_no_tax_and_no_discount():
    assert order_total(10000) == 10000


def test_a_domestic_order_with_a_discount():
    """No tax at this layer domestically, so the total is just the discounted subtotal."""
    assert order_total(10000, discount_pct=10) == 9000


def test_an_international_order_with_tax_and_no_discount():
    assert order_total(10000, discount_pct=0, tax_pct=20) == 12000


def test_an_international_order_taxes_the_discounted_amount():
    """10% off 10000 → 9000; 20% VAT on 9000 → 1800; total 10800."""
    assert order_total(10000, discount_pct=10, tax_pct=20) == 10800


def test_shipping_is_added_after_tax():
    assert order_total(10000, discount_pct=10, tax_pct=20, shipping_cents=500) == 11300


def test_a_fractional_discount_rate():
    """12.5% off 8000 → 7000; 19% VAT on 7000 → 1330; total 8330."""
    assert order_total(8000, discount_pct=12.5, tax_pct=19) == 8330


def test_a_fully_discounted_order_is_free():
    assert order_total(10000, discount_pct=100, tax_pct=20) == 0
