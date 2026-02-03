from __future__ import annotations

import sqlite3
from typing import List

from data_platform.schemas import ProviderStatus


def init_db(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_status (
                name TEXT PRIMARY KEY,
                status TEXT,
                last_success TEXT,
                last_error TEXT,
                last_latency_ms REAL,
                supported_domains TEXT,
                rate_limit TEXT
            )
            """
        )


def upsert_provider_status(db_path: str, status: ProviderStatus) -> None:
    init_db(db_path)
    supported = ",".join(status.supported_domains or [])
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO provider_status
            (name, status, last_success, last_error, last_latency_ms, supported_domains, rate_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                status=excluded.status,
                last_success=excluded.last_success,
                last_error=excluded.last_error,
                last_latency_ms=excluded.last_latency_ms,
                supported_domains=excluded.supported_domains,
                rate_limit=excluded.rate_limit
            """,
            (
                status.name,
                status.status,
                status.last_success,
                status.last_error,
                status.last_latency_ms,
                supported,
                status.rate_limit,
            ),
        )


def list_provider_status(db_path: str) -> List[ProviderStatus]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT name, status, last_success, last_error, last_latency_ms, supported_domains, rate_limit
            FROM provider_status
            """
        ).fetchall()
    out = []
    for row in rows:
        domains = row[5].split(",") if row[5] else None
        out.append(
            ProviderStatus(
                name=row[0],
                status=row[1],
                last_success=row[2],
                last_error=row[3],
                last_latency_ms=row[4],
                supported_domains=domains,
                rate_limit=row[6],
            )
        )
    return out
