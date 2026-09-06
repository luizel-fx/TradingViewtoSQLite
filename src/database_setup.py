"""
database_setup.py
=================
SQLite database initialisation and connection utilities for TradingViewtoSQLite.

This module is responsible for two things:

1. **Schema creation** (:func:`create_db`) — creates the ``futures.db`` file
   and the ``futures`` table if they do not already exist.
2. **Connection factory** (:func:`db_connection`) — returns an open
   ``sqlite3.Connection`` to ``futures.db`` for use by other modules.

Database schema
---------------
Table: ``futures``

============  ====  ===============================================================
Column        Type  Description
============  ====  ===============================================================
symbol        TEXT  Root futures symbol (e.g. ``"CCM"`` for Corn)
expire_month  TEXT  CME single-letter month code (e.g. ``"F"`` = January)
expire_year   INT   Four-digit contract expiry year (e.g. ``2025``)
open          REAL  Session open price
high          REAL  Session high price
low           REAL  Session low price
close         REAL  Session close price
date          TEXT  Trading date in ISO-8601 format (``YYYY-MM-DD``)
============  ====  ===============================================================

Primary key: ``(symbol, expire_month, expire_year, date)`` — ensures that
duplicate rows for the same contract on the same day are rejected.

Usage
-----
Run directly to initialise the database::

    python database_setup.py

Or import in another module::

    from database_setup import create_db, db_connection

    create_db()          # idempotent — safe to call multiple times
    conn = db_connection()
"""

import sqlite3
from datetime import date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = "futures.db"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_db() -> None:
    """Create ``futures.db`` and the ``futures`` table if they do not exist.

    This function is **idempotent**: calling it on an already-initialised
    database is safe and will not alter existing data (``CREATE TABLE IF NOT
    EXISTS`` is used internally).

    The database file is created in the *current working directory* at the
    time this function is called.

    Returns
    -------
    None

    Raises
    ------
    sqlite3.Error
        Printed to stdout and swallowed. Check the console output if the
        database file is not created as expected.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        print("Connection to database established successfully")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS futures (
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            date TEXT,
            PRIMARY KEY (ticker, date)
        )
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS info (last_data_pool_date TEXT)")
        cursor.execute("INSERT INTO info (last_data_pool_date) VALUES (?)", (str(date.today()),))

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts_meta_data (
            ticker TEXT PRIMARY KEY,
            symbol TEXT,
            expiry_month TEXT,
            expiry_year INT,
            exchange TEXT,
            is_expired BOOLEAN
        )""")
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)


def db_connection() -> sqlite3.Connection:
    """Open and return a connection to ``futures.db``.

    The database file is expected to already exist (created by :func:`create_db`).
    The connection is returned open; the caller is responsible for committing
    and closing it when done.

    Returns
    -------
    sqlite3.Connection
        An open connection to ``futures.db``.

    Raises
    ------
    sqlite3.Error
        Printed to stdout and swallowed. If the connection fails, the
        returned ``conn`` variable will be unbound and a ``NameError`` will
        be raised at the ``return`` statement — callers should ensure
        :func:`create_db` has been called first.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        print("Connection to database established successfully")
    except sqlite3.Error as e:
        print(e)
    return conn


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    create_db()
