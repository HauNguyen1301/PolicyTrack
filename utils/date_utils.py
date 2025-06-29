"""Utility functions for parsing and formatting dates consistently across the project.
All dates will be displayed in the Vietnamese standard dd/mm/yyyy format.
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Union

DateLike = Union[str, date, datetime, None]


def _to_date(value: DateLike) -> Optional[date]:
    """Convert *value* to a ``datetime.date`` object if possible.

    The function is defensive and accepts:
    - ``datetime.date`` objects (returned directly)
    - ``datetime.datetime`` objects (date part is returned)
    - Strings in either *YYYY-MM-DD* or *dd/mm/YYYY* formats. If the string
      already contains a slash ('/'), we assume *dd/mm/YYYY*; otherwise we
      attempt *YYYY-MM-DD*.

    Returns ``None`` if the value cannot be parsed.
    """
    if value in (None, "", "None"):
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        val = value.strip().split()[0]  # Bỏ phần thời gian nếu có
        # Thử lần lượt các pattern
        patterns = [
            "%d/%m/%Y", "%Y/%m/%d",  # Dấu gạch chéo
            "%Y-%m-%d", "%d-%m-%Y",   # Dấu gạch ngang
        ]
        for pattern in patterns:
            try:
                return datetime.strptime(val, pattern).date()
            except ValueError:
                continue
        return None

    # Unsupported type
    return None


def format_date(value: DateLike) -> str:
    """Return *value* formatted as ``dd/mm/YYYY``.

    If *value* is ``None`` or cannot be parsed, the original value is returned
    as ``str`` to avoid masking errors.
    """
    dt = _to_date(value)
    if dt is None:
        return str(value) if value is not None else ""
    return dt.strftime("%d/%m/%Y")


def format_date_range(from_value: DateLike, to_value: DateLike, sep: str = " - ") -> str:
    """Return a human-readable date range in the form ``dd/mm/yyyy - dd/mm/yyyy``.

    If one of the ends is missing the function returns "Chưa cập nhật".
    """
    start = format_date(from_value)
    end = format_date(to_value)

    if not start or not end or start.lower() in ("none",) or end.lower() in ("none",):
        return "Chưa cập nhật"
    return f"{start}{sep}{end}"
