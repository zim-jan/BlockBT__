"""
Współbieżność SQLite (audyt 2026-07-17, P1).

WAL dopuszcza 1 pisarza; domyślny ``busy_timeout`` SQLite to 0 ms, więc
równoległe zapisy (dwa joby w tle, job + endpoint) kończyły się natychmiast
``database is locked`` zamiast poczekać na zwolnienie blokady.
"""

from __future__ import annotations


def test_sqlite_busy_timeout_pragma_set():
    import app.db.session as sess

    with sess._engine.connect() as conn:
        value = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()

    assert int(value) >= 5000, (
        f"busy_timeout={value} ms — równoległy pisarz dostaje 'database is locked' "
        "zamiast poczekać na zwolnienie blokady"
    )
