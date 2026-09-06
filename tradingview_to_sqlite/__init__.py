"""
TradingViewtoSQLite
===================
Python library to scrape futures data from TradingView and persist it to a local SQLite database.

Main API:
    - ``setup(symbol_dict)``: Creates tables and loads initial contracts data.
    - ``update_active_contracts()``: Fetches missing days for active contracts and marks expired ones.
    - ``contracts``: Predefined dictionary of standard futures symbols.
    - ``create_db()``: Creates tables in SQLite.
    - ``db_connection()``: Connects to SQLite database.
    - ``load_symbol_data()``: Fetches OHLC bars for a single contract.
    - ``scrapps_and_save()``: Batch scrapes contracts and inserts to database.
"""

from .database_setup import create_db, db_connection
from .load_data import load_symbol_data, load_data_to_db, scrapps_and_save
from .database_update import update_active_contracts
from .contracts import contracts, DEFAULT_CONTRACTS


def setup(symbol_dict: dict = None, db_path: str = "futures.db") -> None:
    """Initialize the SQLite database and seed it with futures contracts data.

    Parameters
    ----------
    symbol_dict : dict, optional
        Dictionary mapping root symbol to ``[exchange, month_codes, years]``.
        If None, the default ``contracts`` dictionary is used.
    db_path : str, optional
        Path to SQLite database file. Defaults to ``"futures.db"``.
    """
    if symbol_dict is None:
        symbol_dict = contracts
    create_db(db_path=db_path)
    scrapps_and_save(symbol_dict, db_path=db_path)


__all__ = [
    "setup",
    "update_active_contracts",
    "contracts",
    "DEFAULT_CONTRACTS",
    "create_db",
    "db_connection",
    "load_symbol_data",
    "load_data_to_db",
    "scrapps_and_save",
]
