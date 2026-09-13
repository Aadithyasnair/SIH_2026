import pytest

try:
    from explainability.geo_summary_generator import generate_geo_summary
except ImportError:
    from sih26146.explainability.geo_summary_generator import generate_geo_summary


def test_geo_summary_single_country():
    """Verify geographic summary for a single country."""
    summary = generate_geo_summary(countries=["Germany"])
    assert "localized to Germany" in summary


def test_geo_summary_multiple_countries_with_timing():
    """Verify geographic summary for multiple countries with time window."""
    summary = generate_geo_summary(
        countries=["Germany", "Netherlands", "United States"],
        time_window_minutes=40.0,
    )
    assert "3 countries within 40 minutes" in summary


def test_geo_summary_from_events():
    """Verify summary extraction from event records."""
    events = [
        {"src_geo_country": "Germany", "dst_geo_country": "Netherlands"},
        {"src_geo_country": "Netherlands", "dst_geo_country": "United States"},
    ]
    summary = generate_geo_summary(events=events, time_window_minutes=15.0)
    assert "3 countries within 15 minutes" in summary


def test_geo_summary_missing_data():
    """Verify fallback for unmapped location data."""
    summary = generate_geo_summary(countries=[])
    assert "unmapped" in summary
