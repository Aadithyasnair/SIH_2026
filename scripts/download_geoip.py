"""
Script to download or verify local MaxMind GeoLite2 databases for SIH26146 offline operation.
Directs database files into shared/geoip/.
"""

import os
import sys
from pathlib import Path

SHARED_GEOIP_DIR = Path(__file__).resolve().parent.parent / "shared" / "geoip"


def check_geoip_status():
    SHARED_GEOIP_DIR.mkdir(parents=True, exist_ok=True)
    city_db = SHARED_GEOIP_DIR / "GeoLite2-City.mmdb"
    country_db = SHARED_GEOIP_DIR / "GeoLite2-Country.mmdb"
    asn_db = SHARED_GEOIP_DIR / "GeoLite2-ASN.mmdb"

    found = []
    missing = []
    for path, name in [(city_db, "GeoLite2-City"), (country_db, "GeoLite2-Country"), (asn_db, "GeoLite2-ASN")]:
        if path.exists():
            found.append(f"{name} ({path.stat().st_size // 1024} KB)")
        else:
            missing.append(name)

    print("=== SIH26146 GeoIP Status ===")
    print(f"Directory: {SHARED_GEOIP_DIR}")
    if found:
        print(f"Installed databases: {', '.join(found)}")
    if missing:
        print(f"Missing databases: {', '.join(missing)}")
        print("\nNote: The system includes a 100% offline deterministic fallback enricher with subnet rules.")
        print("To install official MaxMind databases for high-precision IP geolocation:")
        print("1. Obtain a free license key from https://www.maxmind.com")
        print(f"2. Place GeoLite2-Country.mmdb (or GeoLite2-City.mmdb) and GeoLite2-ASN.mmdb in: {SHARED_GEOIP_DIR}")


if __name__ == "__main__":
    check_geoip_status()
