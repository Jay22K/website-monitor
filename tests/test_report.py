"""Unit tests for the report generation service."""
from datetime import date

from app.services.report import generate_report, SiteRow


def _make_rows():
    return [
        SiteRow("Google", "online", 200, None),
        SiteRow("GitHub", "online", 200, None),
        SiteRow("BrokenSite", "offline", None, "Connection timeout"),
    ]


def test_report_contains_date():
    report = generate_report(_make_rows(), report_date=date(2026, 6, 17))
    assert "2026-06-17" in report


def test_report_counts():
    report = generate_report(_make_rows())
    assert "Total Websites  : 3" in report
    assert "Healthy         : 2" in report
    assert "Failed          : 1" in report


def test_report_online_site():
    report = generate_report(_make_rows())
    assert "Google" in report
    assert "ONLINE" in report


def test_report_offline_site_shows_error():
    report = generate_report(_make_rows())
    assert "BrokenSite" in report
    assert "OFFLINE" in report
    assert "Connection timeout" in report


def test_empty_report():
    report = generate_report([])
    assert "Total Websites  : 0" in report
    assert "Healthy         : 0" in report
