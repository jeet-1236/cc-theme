"""Recording a payment against an invoice (commandcenter/intake.py).

The five shapes below are the same payment typed five ways, and Finance types all five in a normal
morning. The rule under test is that all five record it, and that anything which is NOT an amount comes
back as a 400 naming the field — never a 500, which tells the assistant nothing, pages the on-call, and
loses the payment.
"""
import pytest

from commandcenter.intake import parse_amount, record_payment


def test_a_plain_number_is_an_amount():
    """The one that broke: a round payment typed into a number field arrives as a JSON number."""
    assert parse_amount(1200) == 120000


def test_the_same_amount_typed_as_a_string():
    assert parse_amount("1200") == 120000


def test_the_same_amount_written_the_way_the_remittance_advice_writes_it():
    assert parse_amount("1,200.00") == 120000


def test_the_same_amount_pasted_from_the_bank_statement():
    assert parse_amount("₹1,200.00") == 120000


def test_the_same_amount_pasted_from_a_spreadsheet_cell():
    assert parse_amount("  1200 ") == 120000


def test_paise_are_kept_exactly():
    assert parse_amount("1200.45") == 120045
    assert parse_amount(1200.45) == 120045


def test_a_payment_records_and_says_what_it_recorded():
    status, body = record_payment({"invoice_id": "INV-2291", "amount": 1200})
    assert status == 201
    assert body["amount_cents"] == 120000
    assert body["recorded"] == "₹1,200.00 against INV-2291"


def test_every_shape_records_the_same_payment():
    amounts = [1200, "1200", "1,200.00", "₹1,200.00", "  1200 "]
    recorded = [record_payment({"invoice_id": "INV-2291", "amount": a}) for a in amounts]
    assert all(s == 201 for s, _b in recorded), recorded
    assert len({b["amount_cents"] for _s, b in recorded}) == 1


def test_a_missing_amount_is_a_400_against_the_field():
    status, body = record_payment({"invoice_id": "INV-2291"})
    assert status == 400
    assert body["field"] == "amount"


def test_an_empty_amount_is_a_400_against_the_field():
    status, body = record_payment({"invoice_id": "INV-2291", "amount": "   "})
    assert status == 400
    assert body["field"] == "amount"


def test_a_reference_typed_into_the_amount_box_is_a_400_not_a_crash():
    status, body = record_payment({"invoice_id": "INV-2291", "amount": "INV-2291"})
    assert status == 400
    assert body["field"] == "amount"


def test_a_negative_amount_is_refused():
    with pytest.raises(ValueError):
        parse_amount(-500)


def test_a_missing_invoice_reference_is_a_400_against_that_field():
    status, body = record_payment({"amount": 1200})
    assert status == 400
    assert body["field"] == "invoice_id"


def test_recording_a_payment_never_raises():
    """Whatever is in the box, the assistant gets an answer — not a 500."""
    for bad in (None, "", "   ", "abc", {"nested": 1}, [1, 2], True):
        status, body = record_payment({"invoice_id": "INV-1", "amount": bad})
        assert status == 400, f"{bad!r} should be a 400, got {status}"
        assert "error" in body
