"""cc-code-5 — every HEALTHY status signal must render the brand green, not the danger red."""
from commandcenter import theme


def test_brand_ok_is_defined():
    # baseline (PASS_TO_PASS): the healthy token itself is the Command Center green
    assert theme.BRAND_OK == "#3fb950"


def test_brand_accent_is_defined():
    # baseline (PASS_TO_PASS): the brand accent is still the Command Center blue
    assert theme.BRAND_ACCENT == "#3b82f6"


def test_status_ok_uses_healthy_green():
    # cc-code-5 REPRODUCTION TARGET: fails on the shipped red, passes once healthy status returns the brand green.
    assert theme.status_ok_color() == theme.BRAND_OK, (
        f"healthy status colour is {theme.status_ok_color()!r}, expected the brand green {theme.BRAND_OK!r}")
