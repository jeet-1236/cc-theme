"""commandcenter — the business-logic backend behind the Company Command Center dashboard.

The modules that compute what the dashboard shows and what its forms accept. Each is small, documented and
directly testable, because each is the thing a support ticket ends up pointing at:

    contacts.py   CRM contact intake validation  (the "New CRM contact" form)
    intake.py     POST /api/notes request handling (the "Add note to ticket" form)
    orders.py     order totals — discount, tax, shipping (Revenue · Order totals)
    reports.py    the daily revenue report's day bucketing (Revenue · Daily revenue)

Money is integer cents everywhere. Timestamps are UTC everywhere.
"""
__version__ = "1.0.0"
