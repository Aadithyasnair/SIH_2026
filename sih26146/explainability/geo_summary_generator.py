"""
Geo Summary Generator Module for SIH26146 Explainability Layer (Module D).

Purpose:
Generates concise, plain-language `geo_summary` string values from upstream GeoIP-enriched network metadata.
Runs 100% offline using local GeoIP attributes without live external API calls.
"""

from typing import List, Dict, Any, Optional, Set


def generate_geo_summary(
    countries: Optional[List[str]] = None,
    time_window_minutes: Optional[float] = None,
    events: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generates a concise plain-language geographic summary for an alert record.

    :param countries: Optional explicit list of country names/codes (e.g. ["Germany", "Netherlands", "United States"])
    :param time_window_minutes: Optional duration of the activity in minutes
    :param events: Optional list of network event dictionaries containing src_geo_country / dst_geo_country
    :return: Short plain-language summary string
    """
    unique_countries: Set[str] = set()

    if countries:
        for c in countries:
            if c and c.upper() != "UNKNOWN":
                unique_countries.add(c)

    if events:
        for ev in events:
            src_c = ev.get("src_geo_country")
            dst_c = ev.get("dst_geo_country")
            if src_c and src_c.upper() != "UNKNOWN":
                unique_countries.add(src_c)
            if dst_c and dst_c.upper() != "UNKNOWN":
                unique_countries.add(dst_c)

    country_list = sorted(list(unique_countries))
    country_count = len(country_list)

    if country_count == 0:
        return "Geographic location unmapped (offline network telemetry)"

    if country_count == 1:
        return f"Transaction activity localized to {country_list[0]}"

    if country_count == 2:
        if time_window_minutes is not None and time_window_minutes > 0:
            return f"Funds traced between {country_list[0]} and {country_list[1]} within {int(time_window_minutes)} minutes"
        return f"Funds traced between {country_list[0]} and {country_list[1]}"

    # 3 or more countries
    if time_window_minutes is not None and time_window_minutes > 0:
        return f"Funds traced through IPs in {country_count} countries within {int(time_window_minutes)} minutes"
    else:
        return f"Funds traced through IPs across {country_count} countries"
