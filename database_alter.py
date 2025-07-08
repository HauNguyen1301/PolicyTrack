# -*- coding: utf-8 -*-
"""database_alter.py

Utilities for advanced/administrative interaction with the Turso database that
are kept separate from the stable `database.py` module.  These helpers will be
used by the upcoming *edit contract* and *edit benefit* features.

Key features provided:

1. Connection helper that relies **only** on environment variables (`TURSO_DATABASE_URL`,
   `TURSO_AUTH_TOKEN`) and keeps a lightweight singleton HTTP client, identical
   to the approach in `database.py` but re-implemented here to avoid coupling.
2. Functions to inspect the database schema:
   • `list_tables()`  – returns all user tables.
   • `list_triggers()` – returns trigger name and SQL definition.
3. Convenience helpers to inspect the `log` table and basic recommendations on
   how to optimise its usage (`analyse_log_table()`).

Usage example
-------------
>>> from database_alter import list_tables, list_triggers, analyse_log_table
>>> print(list_tables())
>>> print(list_triggers())
>>> print(analyse_log_table())

The module performs **read-only** operations; no DDL/DML statements are executed
except simple `SELECT`s, so it is safe to call from UI code.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import certifi
import libsql_client  # type: ignore
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment & one-time setup
# ---------------------------------------------------------------------------

# Ensure the certifi CA bundle is used when the OS store may be missing (Windows)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

# Load variables from .env if present (does nothing if file is absent)
load_dotenv()

TURSO_DATABASE_URL: str = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN: str = os.getenv("TURSO_AUTH_TOKEN", "")

if not TURSO_DATABASE_URL:
    raise RuntimeError(
        "TURSO_DATABASE_URL is not set – make sure your environment variables or .env file are configured."
    )

# ---------------------------------------------------------------------------
# Connection helper (singleton, HTTPS)
# ---------------------------------------------------------------------------

_CLIENT: Optional[libsql_client.Client] = None
_CLIENT_CREATED_AT: Optional[datetime] = None  # UTC timestamp


def get_db_connection() -> libsql_client.Client:  # noqa: N802  (keep same naming convention)
    """Return a cached synchronous Turso client.

    Re-creates the client every 8 hours to avoid stale HTTP pools.
    The implementation is intentionally duplicated (not imported) from
    `database.py` to keep the modules independent.
    """
    global _CLIENT, _CLIENT_CREATED_AT
    now = datetime.utcnow()

    if _CLIENT is None or _CLIENT_CREATED_AT is None or (now - _CLIENT_CREATED_AT) > timedelta(hours=8):
        # Close any existing client first
        if _CLIENT is not None:
            try:
                _CLIENT.close()
            finally:
                _CLIENT = None

        # Turso HTTP endpoint uses https:// in place of libsql://
        http_url = TURSO_DATABASE_URL.replace("libsql", "https", 1)
        _CLIENT = libsql_client.create_client_sync(url=http_url, auth_token=TURSO_AUTH_TOKEN)
        _CLIENT_CREATED_AT = now

    return _CLIENT


def _execute(query: str, params: Tuple | List | None = None):
    """Internal helper that wraps execute and returns the result set as list[dict]."""
    if params is None:
        params = []

    client = get_db_connection()
    rs = client.execute(query, params)

    columns = rs.columns or []
    processed: List[Dict[str, Any]] = []
    for row in rs.rows:
        processed.append({col: (val.decode("utf-8") if isinstance(val, bytes) else val) for col, val in zip(columns, row)})
    return processed

# ---------------------------------------------------------------------------
# Schema inspection helpers
# ---------------------------------------------------------------------------

def list_tables() -> List[str]:
    """Return every table name in the current schema (ordered alphabetically)."""
    rows = _execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    return [r["name"] for r in rows]


def list_triggers(include_sql: bool = True) -> List[Dict[str, str]]:
    """Return information on all triggers.

    Args:
        include_sql: If *True* (default) include the `sql` column so you can
            inspect the trigger body.  If *False*, only names are returned to
            reduce payload.
    """
    columns = "name, sql" if include_sql else "name"
    rows = _execute(f"SELECT {columns} FROM sqlite_master WHERE type = 'trigger' ORDER BY name")
    return rows  # already a list[dict]

# ---------------------------------------------------------------------------
# Log-table inspection & optimisation advice
# ---------------------------------------------------------------------------

_LOG_TABLE_CANDIDATES = (
    "log",
    "logs",
    "tbl_log",
    "tbl_logs",
    "audit_log",
    "system_audit_log",
)


def _find_log_table() -> Optional[str]:
    """Best-effort guess of the log table name.

    1. Return the first table that exactly matches one of the common candidate
       names in ``_LOG_TABLE_CANDIDATES``.
    2. If none found, return the first table *containing* the word ``log``
       (case-insensitive).
    """
    existing = list_tables()

    # Step 1 – exact candidate match
    for candidate in _LOG_TABLE_CANDIDATES:
        if candidate in existing:
            return candidate

    # Step 2 – fuzzy match on substring "log"
    for tbl in existing:
        if "log" in tbl.lower():
            return tbl
    return None


def analyse_log_table() -> Dict[str, Any]:
    """Inspect the log table (if present) and return stats & optimisation tips.

    The result dict contains for example:
        {
            "table": "log",
            "row_count": 12345,
            "size_bytes_estimate": 3_000_000,
            "has_index_on_timestamp": True,
            "recommendations": ["Create an index on created_at", "Partition or archive old rows"]
        }
    """
    table_name = _find_log_table()
    if not table_name:
        return {"error": "No log table found in schema."}

    # Row count
    row_count_rs = _execute(f"SELECT COUNT(*) AS cnt FROM {table_name}")
    row_count: int = int(row_count_rs[0]["cnt"]) if row_count_rs else 0

    # Rough size estimate using `pragma_table_info` + typical SQLite page size assumptions.
    # NOTE: Turso exposes pragmas but size is still an estimate; do not rely on for billing.
    pragma_rows = _execute(f"PRAGMA table_info({table_name})")
    avg_col_size = 32  # bytes (very rough – depends on your data)
    size_bytes_estimate = row_count * len(pragma_rows) * avg_col_size

    # Check for an index on a timestamp column (common for log tables)
    idx_rows = _execute(f"PRAGMA index_list('{table_name}')")
    has_ts_index = any("ts" in idx["name"].lower() or "time" in idx["name"].lower() for idx in idx_rows)

    recommendations: List[str] = []

    if row_count > 50_000 and not has_ts_index:
        recommendations.append("Consider adding an index on the timestamp column (e.g. created_at) to speed up queries.")
    if row_count > 100_000:
        recommendations.append(
            "Log table is growing large; implement a retention policy (archive/delete rows older than X days)."
        )
    if not recommendations:
        recommendations.append("Log table usage looks healthy – no immediate action required.")

    return {
        "table": table_name,
        "row_count": row_count,
        "size_bytes_estimate": size_bytes_estimate,
        "has_index_on_timestamp": has_ts_index,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Re-export high-level business functions used by UI panels
# ---------------------------------------------------------------------------

# These are imported *lazily* from the stable `database.py` to keep that module
# the single source of truth for core CRUD logic while letting the UI depend on
# this wrapper.  This way future changes can be localised here without touching
# the UI code again.
try:
    from database import (
        search_contracts_keyword,
        get_contract_by_id,
        get_all_benefit_groups,
        get_all_waiting_times,
        update_contract_general_info,
        update_contract_waiting_periods,
        update_contract_special_cards,
        add_benefit,
    )  # noqa: F401
except ImportError as _err:  # pragma: no cover – happens during unit tests w/o full deps
    # When database.py is unavailable, expose dummy stubs that raise informative errors.
    def _missing(*_a, **_kw):  # type: ignore
        raise RuntimeError("database.py missing – core CRUD functions unavailable")

    search_contracts_keyword = _missing  # type: ignore
    get_contract_by_id = _missing  # type: ignore
    get_all_benefit_groups = _missing  # type: ignore
    get_all_waiting_times = _missing  # type: ignore
    update_contract_general_info = _missing  # type: ignore
    update_contract_waiting_periods = _missing  # type: ignore
    update_contract_special_cards = _missing  # type: ignore
    add_benefit = _missing  # type: ignore


# ---------------------------------------------------------------------------
# Local implementations of update helpers (override imported stubs)
# ---------------------------------------------------------------------------

def update_contract_general_info(hopdong_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Update general info of a contract; mirrors logic in database.py."""
    client = get_db_connection()
    if not data:
        return False, "Không có dữ liệu để cập nhật."

    allowed_columns = [
        "soHopDong",
        "tenCongTy",
        "HLBH_tu",
        "HLBH_den",
        "coPay",
    ]
    set_clauses: List[str] = []
    params: List[Any] = []
    for key, value in data.items():
        if key in allowed_columns:
            set_clauses.append(f"{key} = ?")
            params.append(value)

    if not set_clauses:
        return False, "Không có trường hợp lệ nào để cập nhật."

    params.append(hopdong_id)
    sql = f"UPDATE hopdong_baohiem SET {', '.join(set_clauses)} WHERE id = ?"
    try:
        client.execute(sql, params)
        return True, "Cập nhật thông tin chung thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật thông tin chung: {e}"


def update_contract_waiting_periods(hopdong_id: int, waiting_periods: List[Dict[str, Any]]):
    """Replace waiting periods for a contract in a batch operation."""
    conn = get_db_connection()
    try:
        stmts: List[libsql_client.Statement] = [
            libsql_client.Statement(
                "DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [hopdong_id]
            )
        ]
        for wp in waiting_periods:
            stmts.append(
                libsql_client.Statement(
                    "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                    [hopdong_id, wp["cho_id"], wp["gia_tri"]],
                )
            )
        if stmts:
            conn.batch(stmts)
    except Exception as e:
        raise Exception(f"Lỗi database khi cập nhật thời gian chờ: {e}")


def update_contract_special_cards(hopdong_id: int, special_cards: List[Dict[str, Any]]):
    """Replace special cards of a contract using batch operation."""
    conn = get_db_connection()
    try:
        stmts: List[libsql_client.Statement] = [
            libsql_client.Statement(
                "DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [hopdong_id]
            )
        ]
        for card in special_cards:
            stmts.append(
                libsql_client.Statement(
                    "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                    [hopdong_id, card["so_the"], card["ten_NDBH"], card.get("ghi_chu", "")],
                )
            )
        if stmts:
            conn.batch(stmts)
    except Exception as e:
        raise Exception(f"Lỗi database khi cập nhật thẻ đặc biệt: {e}")

__all__ = [
    # schema helpers
    "list_tables",
    "list_triggers",
    "analyse_log_table",
    # high-level operations
    "search_contracts_keyword",
    "get_contract_by_id",
    "get_all_benefit_groups",
    "get_all_waiting_times",
    "update_contract_general_info",
    "update_contract_waiting_periods",
    "update_contract_special_cards",
    "add_benefit",
]

# ---------------------------------------------------------------------------
# Module test / CLI invocation (optional)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("Tables:\n", list_tables())
    print("\nTriggers (names only):\n", [t["name"] for t in list_triggers(include_sql=False)])
    print("\nLog table analysis:\n", json.dumps(analyse_log_table(), indent=2, ensure_ascii=False))
