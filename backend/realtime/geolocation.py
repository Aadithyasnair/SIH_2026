"""
geolocation.py - IP to Country / Region lookup with SQLite caching and rate-limiting.
"""

import time
import requests
from typing import Dict, Any, Optional
from backend.realtime.database import get_cached_ip, set_cached_ip

_session = requests.Session()
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 0.4  # ~45 req/min rate limit safety

def is_private_or_reserved_ip(ip: str) -> bool:
    if not ip or ip in ("127.0.0.1", "localhost", "0.0.0.0"):
        return True
    parts = ip.split(".")
    if len(parts) == 4:
        try:
            first, second = int(parts[0]), int(parts[1])
            if first == 10:
                return True
            if first == 172 and 16 <= second <= 31:
                return True
            if first == 192 and second == 168:
                return True
        except ValueError:
            pass
    return False

def resolve_ip(ip: str, timeout: float = 3.5) -> Dict[str, Any]:
    global _last_request_time

    if not ip or is_private_or_reserved_ip(ip):
        return {
            "ip": ip or "0.0.0.0",
            "country": "Local / Private Network",
            "country_code": "LOC",
            "city": "Internal",
            "org": "Private / Loopback"
        }

    # Check database cache first
    try:
        cached = get_cached_ip(ip)
        if cached:
            return cached
    except Exception:
        pass

    # Rate limiting delay
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

    # Query ip-api.com
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,org,as,query"
    try:
        _last_request_time = time.time()
        resp = _session.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                geo_info = {
                    "ip": ip,
                    "country": data.get("country", "Unknown"),
                    "country_code": data.get("countryCode", "??"),
                    "city": data.get("city", "Unknown"),
                    "org": data.get("org") or data.get("as") or "Unknown"
                }
                try:
                    set_cached_ip(ip, geo_info)
                except Exception:
                    pass
                return geo_info
    except Exception:
        pass

    fallback = {
        "ip": ip,
        "country": "Unknown",
        "country_code": "??",
        "city": "Unknown",
        "org": "Unknown"
    }
    return fallback
