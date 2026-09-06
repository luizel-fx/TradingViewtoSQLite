"""
load_initial_data.py
====================
Utilities for scraping futures price data from TradingView and persisting
it to the local SQLite database.

Workflow
--------
1. ``load_symbol_data`` — builds a TradingView ticker string, fetches OHLC
   bars via ``price_loaders.tradingview``, and returns a clean DataFrame.
2. ``load_data_to_db`` — calls ``load_symbol_data`` and inserts each row
   into the ``futures`` table through a live database connection.
3. ``scrapps_and_save`` — iterates over a symbol dictionary and delegates
   each contract to ``load_data_to_db``.

Typical usage
-------------
::

    from load_initial_data import scrapps_and_save

    symbol_dict = {
        "CCM": [
            "BMFBOVESPA",
            ["F", "H", "K", "N"],               # expiry month codes
            [2020, 2021, 2022, 2023, 2024, 2025, 2026],  # expiry years
        ]
    }
    scrapps_and_save(symbol_dict)

Dependencies
------------
- ``price_loaders.tradingview`` — TradingView data fetcher
- ``database_setup.db_connection`` — returns an open ``sqlite3.Connection``
- ``pandas`` — DataFrame manipulation
"""

from price_loaders.tradingview import load_asset_price
from datetime import date, timedelta    
from database_setup import db_connection
import pandas as pd


def load_symbol_data(exchange:str, symbol: str, expire_month: str, expire_year: int, backward_days: int = 10_000) -> pd.DataFrame:
    """Fetch daily OHLC data for a single futures contract from TradingView.

    Constructs the TradingView ticker by concatenating *symbol*, *expire_month*,
    and *expire_year* (e.g. ``"CCM"`` + ``"F"`` + ``2025`` → ``"CCMF2025"``),
    retrieves up to 10 000 daily bars, and returns a normalised DataFrame ready
    for database insertion.

    Parameters
    ----------
    symbol : str
        Root symbol of the futures contract (e.g. ``"CCM"`` for Corn).
    expire_month : str
        Single-letter CME month code (e.g. ``"F"`` = January, ``"H"`` = March).
    expire_year : int
        Four-digit expiry year (e.g. ``2025``).
    backward_days : int, optional
        Number of days to go back in time to fetch data for the contract. Defaults to ``10_000``.

    Returns
    -------
    tuple
        Tuple containing:   
        - pd.DataFrame: DataFrame with the following columns, in order:

        ============  =======  ==========================================
        Column        Type     Description
        ============  =======  ==========================================
        ticker        str      Root futures symbol
        open          float    Session open price
        high          float    Session high price
        low           float    Session low price
        close         float    Session close price
        date          date     Trading date (``datetime.date`` object)
        ============  =======  ==========================================
    """
    ticker = f'{exchange}:{symbol}{expire_month}{expire_year}'
    data = load_asset_price(ticker, backward_days, "1D")
    data = data.rename(columns={'time': 'date'})
    data['date'] = data['date'].apply(lambda x: date(x.year, x.month, x.day))
    data = data.assign(ticker=ticker)

    return data[['ticker', 'open', 'high', 'low', 'close', 'date']]


def load_data_to_db(exchange: str, symbol: str, expire_month: str, expire_year: int, backward_days: int = 10_000) -> None:
    """Scrape one futures contract and insert all rows into the database.

    Opens a connection to the SQLite database via :func:`database_setup.db_connection`,
    fetches the contract data with :func:`load_symbol_data`, and inserts each
    row into the ``futures`` table using a parameterised ``INSERT`` statement.

    Duplicate rows are silently ignored because the table's primary key is
    ``(symbol, expire_month, expire_year, date)``.

    Parameters
    ----------
    symbol : str
        Root symbol of the futures contract (e.g. ``"CCM"``).
    expire_month : str
        CME month code for the contract expiry (e.g. ``"F"``).
    expire_year : int
        Four-digit expiry year (e.g. ``2025``).

    Raises
    ------
    sqlite3.Error
        Propagated from the underlying database connection or cursor if an
        unexpected database error occurs.
    RuntimeError
        Propagated from :func:`load_symbol_data` / ``load_asset_price`` if
        TradingView returns no data for the requested ticker.
    """
    conn = db_connection()
    cursor = conn.cursor()

    ticker = f"{exchange}:{symbol}{expire_month}{expire_year}"

    last_data_pool = pd.read_sql("SELECT last_data_pool_date FROM info", conn).iloc[0]['last_data_pool_date']

    data = load_symbol_data(exchange, symbol, expire_month, expire_year, backward_days)
    last_symbol_date = data['date'].max()

    if last_symbol_date < last_data_pool+timedelta(days=10):
       expired = True
    else:
        expired = False

    data.apply(
        lambda x: cursor.execute("""
            INSERT INTO futures (
                ticker,
                open,
                high,
                low,
                close,
                date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, x),
        axis=1,
    )

    cursor.execute("""
    INSERT INTO contracts_meta_data (
        ticker,
        symbol,
        expiry_month,
        expiry_year,
        exchange,
        is_expired
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (ticker, symbol, expire_month, expire_year, exchange, expired))

    conn.commit()
    conn.close()


def scrapps_and_save(symbol_dict: dict) -> None:
    """Scrape multiple futures contracts and persist them to the database.

    Iterates over every ``(symbol, expire_month, expire_year)`` combination
    defined in *symbol_dict* and delegates each to :func:`load_data_to_db`.

    Parameters
    ----------
    symbol_dict : dict
        Mapping of root symbol → ``[month_codes, years]`` where:

        * ``month_codes`` is a list of CME single-letter month codes.
        * ``years`` is a list of four-digit expiry years.

        Every combination of ``(month_code, year)`` is loaded via
        :func:`zip`, so both lists are consumed in parallel — they do **not**
        produce a full Cartesian product.

        Example::

            symbol_dict = {
                "CCM": [
                    "BMFBOVESPA",
                    ["F", "H", "K", "N"],
                    [2020, 2021, 2022, 2023, 2024, 2025, 2026],
                ]
            }

    Returns
    -------
    None
    """
    for symbol in symbol_dict:
        exchange = symbol_dict[symbol][0]
        for expire_month, expire_year in zip(symbol_dict[symbol][1], symbol_dict[symbol][2]):
            load_data_to_db(exchange, symbol, expire_month, expire_year)