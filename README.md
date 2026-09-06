# TradingViewtoSQLite

A Python library to scrape futures price data from TradingView and persist it directly into a local SQLite database (`futures.db`). Designed to be installed as a package and seamlessly integrated into quantitative trading, backtesting, or data pipeline projects.

---

## Features

- **Installable via pip**: Use directly as a dependency in your own Python projects.
- **One-Call Database Setup & Seeding**: Initialize schemas and download multi-year historical contract series with a single function call.
- **Delta/Incremental Updates**: Automatically checks `MAX(date)` for each active contract, computes the missing day gap, and fetches only the delta from TradingView.
- **Expiration Detection**: Detects when contracts have stopped trading and flags them as expired (`is_expired = 1`).

---

## Installation

Install directly from GitHub via `pip`:

```bash
pip install git+https://github.com/luizel-fx/TradingViewtoSQLite.git
```

Or install locally in editable mode for development:

```bash
git clone https://github.com/luizel-fx/TradingViewtoSQLite.git
cd TradingViewtoSQLite
pip install -e .
```

---

## Quick Start

### 1. Initial Setup & Seeding
```python
from tradingview_to_sqlite.database_setup import create_db
from tradingview_to_sqlite.load_data import scrapps_and_save
from tradingview_to_sqlite.database_update import update_active_contracts

# Starts creating the database
create_db()

# and make a dictionary containing the contracts wanted 
contracts = {
    "CCM": [
        "BMFBOVESPA",
        ["F", "H", "K", "N", "U", "X"],               # Jan, Mar, Mai, Jul, Set, Nov
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "BGI": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "DI1": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ]
}

# then you executes
scrapps_and_save(contracts)
```
The contract dictionaty must have the following structure:

{
    asset: [
        exchange,
        list_of_expire_months,
        list_of_expire_years
    ]
}

### 2. Daily Incremental Updates

```python
# If you need to update the database...

update_active_contracts()

# And to add contracts that are not in the database yet, just execute

new_contracts = {
    "DOL": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"], # Todos os meses
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZS": [
        "CBOT",
        ["F", "H", "K", "N", "Q", "U", "X"],          # Jan, Mar, Mai, Jul, Ago, Set, Nov
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ],
    "ZC": [
        "CBOT",
        ["H", "K", "N", "U", "Z"],                    # Mar, Mai, Jul, Set, Dez
        [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    ]
}

scrapps_and_save(new_contracts)
```

## Querying Price Data

Since data is stored in standard SQLite format, you can query it using pandas or sqlite3:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("futures.db")

# Read historical price data for a specific contract
df = pd.read_sql(
    "SELECT * FROM futures WHERE ticker = 'BMFBOVESPA:CCMF2025' ORDER BY date ASC",
    conn,
    parse_dates=["date"]
)
print(df.head())

# Query list of active contracts
active_df = pd.read_sql(
    "SELECT * FROM contracts_meta_data WHERE is_expired = 0",
    conn
)
print(active_df)

conn.close()
```

---

## Database Schema

### `futures`
| Column | Type | Description |
| :--- | :--- | :--- |
| `ticker` | `TEXT` | Full TradingView ticker (e.g., `BMFBOVESPA:CCMF2025`) |
| `open` | `REAL` | Session opening price |
| `high` | `REAL` | Session high price |
| `low` | `REAL` | Session low price |
| `close` | `REAL` | Session closing price |
| `date` | `TEXT` | Trading session date (`YYYY-MM-DD`) |

*Primary Key:* `(ticker, date)`

### `contracts_meta_data`
| Column | Type | Description |
| :--- | :--- | :--- |
| `ticker` | `TEXT` | Contract ticker identifier (`PRIMARY KEY`) |
| `symbol` | `TEXT` | Underlying root symbol (e.g., `CCM`) |
| `expiry_month`| `TEXT` | CME month letter code (e.g., `F`, `H`, etc.) |
| `expiry_year` | `INT` | 4-digit contract delivery year (e.g., `2025`) |
| `exchange` | `TEXT` | Exchange name (e.g., `BMFBOVESPA`) |
| `is_expired` | `BOOLEAN` | `0` (active) or `1` (expired) |

### `info`
| Column | Type | Description |
| :--- | :--- | :--- |
| `last_data_pool_date` | `TEXT` | Date of the latest data update pool |

---

## API Reference

```python
from tradingview_to_sqlite import (
    setup,                   # setup(symbol_dict=None, db_path="futures.db")
    update_active_contracts, # update_active_contracts(db_path="futures.db")
    contracts,               # Predefined universe dictionary
    create_db,               # create_db(db_path="futures.db")
    db_connection,           # db_connection(db_path="futures.db")
    load_symbol_data,        # load_symbol_data(exchange, symbol, expire_month, expire_year, backward_days=10000)
    load_data_to_db,         # load_data_to_db(exchange, symbol, expire_month, expire_year, backward_days=10000, db_path="futures.db")
    scrapps_and_save,        # scrapps_and_save(symbol_dict, db_path="futures.db")
)
```

---

## License

MIT License.
