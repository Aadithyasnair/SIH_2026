"""
Time Aligner Module for SIH26146 Data Ingestion
Normalizes all timestamps to standard ISO8601 UTC string format.
"""

from datetime import datetime, timezone
import dateutil.parser


def normalize_timestamp(raw_timestamp: str | int | float) -> str:
    """
    Converts various timestamp formats into a standardized ISO8601 UTC string.
    Supported inputs:
    - Unix epoch timestamp (int or float, in seconds or milliseconds)
    - ISO8601 strings (e.g. '2026-01-15T08:37:00Z', '2026-01-15 08:37:00+00:00')
    - Custom datetime strings parseable by dateutil
    """
    if raw_timestamp is None:
        raise ValueError("Timestamp cannot be None")

    if isinstance(raw_timestamp, (int, float)):
        ts_val = float(raw_timestamp)
        # If timestamp is in milliseconds (e.g. > 1e11), convert to seconds
        if ts_val > 1e11:
            ts_val /= 1000.0
        dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
        return dt.isoformat()

    if isinstance(raw_timestamp, str):
        cleaned = raw_timestamp.strip()
        if not cleaned:
            raise ValueError("Empty timestamp string")

        # Try parsing as float/int timestamp string
        try:
            ts_val = float(cleaned)
            if ts_val > 1e11:
                ts_val /= 1000.0
            dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass

        # Parse string using dateutil
        try:
            dt = dateutil.parser.parse(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat()
        except Exception as e:
            raise ValueError(f"Failed to parse timestamp '{raw_timestamp}': {e}") from e

    raise ValueError(f"Unsupported timestamp type: {type(raw_timestamp)}")
