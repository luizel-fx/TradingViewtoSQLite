"""
database_setup.py
=================
SQLite database initialisation and connection utilities for TradingViewtoSQLite.

This module provides:
1. **create_db**: Creates the tables (futures, contracts_meta_data, info) in futures.db.
2. **db_connection**: Returns an open sqlite3.Connection to futures.db.
"""

import sqlite3
from datetime import date

DB_PATH = "futures.db"


def create_db(db_path: str = DB_PATH) -> None:
    """Create ``futures.db`` and the necessary tables if they do not exist.

    Tables created:
    - ``futures``: Stores OHLC daily bars for futures contracts.
    - ``contracts_meta_data``: Stores contract metadata and expiration status.
    - ``info``: Stores metadata such as last data pool date.

    Parameters
    ----------
    db_path : str, optional
        Path to the SQLite database file. Defaults to ``"futures.db"``.
    """
    try:
        conn = sqlite3.connect(db_path)
        print(f"Connected to database '{db_path}'")
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
        cursor.execute("SELECT COUNT(*) FROM info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO info (last_data_pool_date) VALUES (?)", (str(date.today()),))

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts_meta_data (
            ticker TEXT PRIMARY KEY,
            symbol TEXT,
            expiry_month TEXT,
            expiry_year INT,
            exchange TEXT,
            is_expired BOOLEAN
        )
        """)

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database setup error: {e}")


def db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open and return a connection to the SQLite database.

    Parameters
    ----------
    db_path : str, optional
        Path to the SQLite database file. Defaults to ``"futures.db"``.

    Returns
    -------
    sqlite3.Connection
        An open connection to the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database '{db_path}': {e}")
        raise
