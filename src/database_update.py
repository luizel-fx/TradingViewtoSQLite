"""
database_update.py
==================
Incremental update utility for TradingViewtoSQLite.

Instead of re-fetching full history, this module reads the ``contracts_meta_data``
table to discover all active (non-expired) contracts, calculates exactly how
many calendar days of data are missing for each one, fetches only that window
via :func:`load_initial_data.load_symbol_data`, and persists the new bars.

It also checks whether any contract has ceased trading (expired) and marks it
as expired in ``contracts_meta_data``, and updates the ``info`` table with today's
pool date.

Workflow
--------
1. Query ``contracts_meta_data`` for rows where ``is_expired = 0`` (or ``False``).
2. For each active contract, query ``MAX(date)`` from the ``futures`` table.
3. Compute ``days_missing = (today - max_date).days``.
4. If ``days_missing > 0``, call :func:`load_initial_data.load_symbol_data` with
   ``backward_days = days_missing`` to retrieve only missing bars.
5. Insert new price records into ``futures`` using ``INSERT OR IGNORE``.
6. Check if the contract is expired: if the contract's latest trading date is older
   than a threshold (default: 10 days before today), update ``contracts_meta_data``
   setting ``is_expired = 1``.
7. Update ``info.last_data_pool_date`` to today's date.

Typical usage
-------------
::

    python src/database_update.py

Dependencies
------------
- ``load_initial_data.load_symbol_data`` — TradingView OHLC fetcher
- ``database_setup.db_connection`` — SQLite connection factory
- ``pandas`` — DataFrame manipulation
"""

import sys
import os
from datetime import date, timedelta

import pandas as pd

# Ensure the src/ directory is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_setup import db_connection
from load_initial_data import load_symbol_data

# Threshold in days to consider a contract expired if no trades have occurred
EXPIRATION_THRESHOLD_DAYS = 10


def update_active_contracts() -> None:
    """Fetch and insert missing price data for all non-expired contracts.

    Reads ``contracts_meta_data`` to find every contract where ``is_expired = 0``,
    determines the most recent date stored in ``futures`` for each contract,
    and fetches only the missing days up to today using :func:`load_symbol_data`.

    If a contract's latest date remains older than ``EXPIRATION_THRESHOLD_DAYS``
    behind today, it is marked as expired in ``contracts_meta_data``.

    Finally, updates ``info.last_data_pool_date`` with today's date.

    Returns
    -------
    None
    """
    conn = db_connection()
    cursor = conn.cursor()
    today = date.today()

    # ------------------------------------------------------------------
    # 1. Load all active (non-expired) contracts
    # ------------------------------------------------------------------
    active_contracts = pd.read_sql(
        "SELECT ticker, symbol, expiry_month, expiry_year, exchange "
        "FROM contracts_meta_data "
        "WHERE is_expired = 0 OR is_expired IS NULL",
        conn,
    )

    if active_contracts.empty:
        print("No active contracts found in contracts_meta_data. Nothing to update.")
    else:
        print(f"Found {len(active_contracts)} active contract(s) to update.")

        for _, contract in active_contracts.iterrows():
            ticker       = contract["ticker"]
            symbol       = contract["symbol"]
            expiry_month = contract["expiry_month"]
            expiry_year  = int(contract["expiry_year"])
            exchange     = contract["exchange"]

            # ------------------------------------------------------------------
            # 2. Find the most recent date already in futures for this ticker
            # ------------------------------------------------------------------
            result = pd.read_sql(
                "SELECT MAX(date) AS max_date FROM futures WHERE ticker = ?",
                conn,
                params=(ticker,),
            )
            max_date_val = result.iloc[0]["max_date"]

            if max_date_val is None:
                print(
                    f"  [{ticker}] No existing rows in futures — skipping "
                    "(run initial setup first)."
                )
                continue

            if isinstance(max_date_val, str):
                max_date = date.fromisoformat(max_date_val)
            else:
                max_date = max_date_val

            # ------------------------------------------------------------------
            # 3. Calculate the gap in days
            # ------------------------------------------------------------------
            days_missing = (today - max_date).days
            latest_date = max_date

            if days_missing <= 0:
                print(f"  [{ticker}] Already up to date (max date: {max_date}).")
            else:
                print(
                    f"  [{ticker}] Last date: {max_date} — fetching {days_missing} day(s) of data..."
                )

                # --------------------------------------------------------------
                # 4. Fetch missing window via load_symbol_data
                # --------------------------------------------------------------
                try:
                    new_data = load_symbol_data(
                        exchange=exchange,
                        symbol=symbol,
                        expire_month=expiry_month,
                        expire_year=expiry_year,
                        backward_days=days_missing,
                    )
                except Exception as err:
                    print(f"  [{ticker}] Error fetching data: {err}")
                    new_data = None

                if new_data is not None and not new_data.empty:
                    # Keep only rows newer than max_date to prevent duplicates
                    new_rows = new_data[new_data["date"] > max_date]

                    if not new_rows.empty:
                        new_rows.apply(
                            lambda row: cursor.execute("""
                                INSERT OR IGNORE INTO futures (
                                    ticker,
                                    open,
                                    high,
                                    low,
                                    close,
                                    date
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                row["ticker"],
                                row["open"],
                                row["high"],
                                row["low"],
                                row["close"],
                                str(row["date"]),
                            )),
                            axis=1,
                        )
                        conn.commit()
                        print(f"  [{ticker}] Inserted {len(new_rows)} new row(s).")

                    latest_date = new_data["date"].max()
                    if isinstance(latest_date, str):
                        latest_date = date.fromisoformat(latest_date)

            # ------------------------------------------------------------------
            # 5. Check if contract has expired & update contracts_meta_data
            # ------------------------------------------------------------------
            if latest_date < today - timedelta(days=EXPIRATION_THRESHOLD_DAYS):
                print(
                    f"  [{ticker}] Contract appears expired (last trading date: {latest_date}). "
                    "Updating contracts_meta_data (is_expired = 1)..."
                )
                cursor.execute("""
                    UPDATE contracts_meta_data
                    SET is_expired = 1
                    WHERE ticker = ? OR (symbol = ? AND expiry_month = ? AND expiry_year = ?)
                """, (ticker, symbol, expiry_month, expiry_year))
                conn.commit()

    # ------------------------------------------------------------------
    # 6. Update the info table with today's pool date
    # ------------------------------------------------------------------
    today_str = str(today)
    cursor.execute("SELECT COUNT(*) FROM info")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute("INSERT INTO info (last_data_pool_date) VALUES (?)", (today_str,))
    else:
        cursor.execute("UPDATE info SET last_data_pool_date = ?", (today_str,))

    conn.commit()
    print(f"\nUpdated info table: last_data_pool_date = {today_str}")

    conn.close()
    print("Update complete.")


if __name__ == "__main__":
    update_active_contracts()
