"""
load_initial_data.py
====================
Utilities for scraping futures price data from TradingView and persisting
it to the local SQLite database.
"""

from datetime import date, timedelta
import pandas as pd
from price_loaders.tradingview import load_asset_price

try:
    from .database_setup import db_connection
except ImportError:
    from database_setup import db_connection


def load_symbol_data(
    exchange: str,
    symbol: str,
    expire_month: str,
    expire_year: int,
    backward_days: int = 10_000,
) -> pd.DataFrame:
    """Fetch daily OHLC data for a single futures contract from TradingView.

    Parameters
    ----------
    exchange : str
        Exchange name (e.g. ``"BMFBOVESPA"``, ``"CBOT"``, ``"CME"``, ``"NYMEX"``).
    symbol : str
        Root symbol of the futures contract (e.g. ``"CCM"``).
    expire_month : str
        Single-letter CME month code (e.g. ``"F"``, ``"H"``, etc.).
    expire_year : int
        Four-digit expiry year (e.g. ``2025``).
    backward_days : int, optional
        Number of days of history to fetch. Defaults to ``10_000``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ``['ticker', 'open', 'high', 'low', 'close', 'date']``.
    """
    ticker = f"{exchange}:{symbol}{expire_month}{expire_year}"
    data = load_asset_price(ticker, backward_days, "1D")
    data = data.rename(columns={"time": "date"})
    data["date"] = data["date"].apply(lambda x: date(x.year, x.month, x.day))
    data = data.assign(ticker=ticker)

    return data[["ticker", "open", "high", "low", "close", "date"]]


def load_data_to_db(
    exchange: str,
    symbol: str,
    expire_month: str,
    expire_year: int,
    backward_days: int = 10_000,
    db_path: str = "futures.db",
) -> None:
    """Scrape one futures contract and insert all rows into the database."""
    conn = db_connection(db_path)
    cursor = conn.cursor()

    ticker = f"{exchange}:{symbol}{expire_month}{expire_year}"

    info_df = pd.read_sql("SELECT last_data_pool_date FROM info", conn)
    if not info_df.empty:
        last_data_pool_val = info_df.iloc[0]["last_data_pool_date"]
        if isinstance(last_data_pool_val, str):
            last_data_pool = date.fromisoformat(last_data_pool_val)
        else:
            last_data_pool = last_data_pool_val
    else:
        last_data_pool = date.today()

    data = load_symbol_data(exchange, symbol, expire_month, expire_year, backward_days)
    if data is None or data.empty:
        print(f"  [{ticker}] No data returned.")
        conn.close()
        return

    last_symbol_date = data["date"].max()
    if isinstance(last_symbol_date, str):
        last_symbol_date = date.fromisoformat(last_symbol_date)

    if last_symbol_date < last_data_pool - timedelta(days=10):
        expired = True
        expiration_date = last_symbol_date
    else:
        expired = False
        expiration_date = None

    data.apply(
        lambda x: cursor.execute(
            """
            INSERT OR IGNORE INTO futures (
                ticker,
                open,
                high,
                low,
                close,
                date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (x["ticker"], x["open"], x["high"], x["low"], x["close"], str(x["date"])),
        ),
        axis=1,
    )

    cursor.execute(
        """
    INSERT OR REPLACE INTO contracts_meta_data (
        ticker,
        symbol,
        expiry_month,
        expiry_year,
        exchange,
        is_expired,
        expiration_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (ticker, symbol, expire_month, expire_year, exchange, expired, str(expiration_date)),
    )

    conn.commit()
    conn.close()


def scraping_and_save(symbol_dict: dict, db_path: str = "futures.db") -> None:
    """Scrape multiple futures contracts and persist them to the database.

    Parameters
    ----------
    symbol_dict : dict
        Mapping of root symbol -> ``[exchange, month_codes, years]``.
    db_path : str, optional
        Path to SQLite database file.
    """
    for symbol, details in symbol_dict.items():
        exchange = details[0]
        months = details[1]
        years = details[2]
        print(f"Processing symbol '{symbol}' from '{exchange}'...")
        for expire_month in months:
            for expire_year in years:
                try:
                    load_data_to_db(exchange, symbol, expire_month, expire_year, db_path=db_path)
                except Exception as e:
                    print(f"  Error loading {exchange}:{symbol}{expire_month}{expire_year}: {e}")
