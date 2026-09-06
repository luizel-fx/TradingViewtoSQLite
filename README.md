# TradingViewtoSQLite

A modular Python utility to scrape historical and ongoing futures price data from TradingView and persist it in a local SQLite database (`futures.db`). It supports automatic initial loading as well as intelligent, incremental daily updates that track active vs. expired contracts.

---

## Features

- **One-Command Setup**: Initialize the database and populate initial historical data in a single run.
- **Incremental Updates**: Calculates the missing calendar day gap for each active contract and fetches only the delta from TradingView.
- **Contract Expiration Detection**: Automatically marks contracts as expired (`is_expired = 1`) when trading has stopped.
- **Metadata Tracking**: Maintains metadata about contracts, exchanges, and data ingestion timestamps.
- **Idempotent Operations**: Safe to re-run; uses `INSERT OR IGNORE` and `INSERT OR REPLACE` to avoid duplicate rows.

---

## Database Schema

The SQLite database file `futures.db` is organized into three tables:

### 1. `futures`
Stores historical OHLC daily price bars.

| Column | Type | Description |
| :--- | :--- | :--- |
| `ticker` | `TEXT` | Full TradingView ticker (e.g., `BMFBOVESPA:CCMF2025`) |
| `open` | `REAL` | Session opening price |
| `high` | `REAL` | Session high price |
| `low` | `REAL` | Session low price |
| `close` | `REAL` | Session closing price |
| `date` | `TEXT` | Trading session date in ISO format (`YYYY-MM-DD`) |

*Primary Key:* `(ticker, date)`

### 2. `contracts_meta_data`
Tracks known futures contracts and expiration status.

| Column | Type | Description |
| :--- | :--- | :--- |
| `ticker` | `TEXT` | Contract ticker identifier (`PRIMARY KEY`) |
| `symbol` | `TEXT` | Underlying root symbol (e.g., `CCM`) |
| `expiry_month`| `TEXT` | CME month letter code (e.g., `F`, `H`, `K`, `N`, `U`, `X`, `Z`) |
| `expiry_year` | `INT` | 4-digit contract delivery year (e.g., `2025`) |
| `exchange` | `TEXT` | Exchange name (e.g., `BMFBOVESPA`) |
| `is_expired` | `BOOLEAN` | `0` (`False`) if contract is active, `1` (`True`) if expired |

### 3. `info`
Stores general execution metadata and synchronization logs.

| Column | Type | Description |
| :--- | :--- | :--- |
| `last_data_pool_date` | `TEXT` | Date of the latest data fetch / update pool |

---

## Project Structure

```
TradingViewtoSQLite/
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── src/
    ├── database_setup.py       # Table creation (create_db) & connection helper (db_connection)
    ├── load_initial_data.py    # TradingView scraper & initial batch loader
    ├── database_update.py      # Incremental daily update script
    └── setup.py                # Single-command database initialization & seed runner
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/luizel-fx/TradingViewtoSQLite.git
   cd TradingViewtoSQLite
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv

   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1

   # On Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Initial Setup & Seeding

To create the SQLite database schema and perform the initial ingestion:

```bash
python src/setup.py
```

This runs:
- `create_db()` to build `futures.db` and its tables.
- `scrapps_and_save()` to download historical bars and metadata for default contract series.

### 2. Incremental Daily Updates

Once initialized, keep your database current without re-downloading entire histories:

```bash
python src/database_update.py
```

**How the update works:**
1. Queries `contracts_meta_data` for all unexpired contracts (`is_expired = 0`).
2. Finds the most recent date stored in `futures` for each contract (`MAX(date)`).
3. Computes the missing day gap: `days_missing = (today - max_date).days`.
4. Calls `load_symbol_data` requesting only the missing days.
5. Checks if the contract has ceased trading (last date > 10 days in the past) and marks `is_expired = 1`.
6. Updates `info.last_data_pool_date` to today's date.

---

## Customizing Contract Configuration

You can specify which symbols and contract maturities to scrape in Python:

```python
from load_initial_data import scrapps_and_save

# Example: Custom dictionary of commodities/futures
symbols = {
    "CCM": [
        "BMFBOVESPA",
        ["F", "H", "K", "N", "U", "X"],
        [2023, 2024, 2025, 2026],
    ],
    "BGI": [
        "BMFBOVESPA",
        ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"],
        [2024, 2025, 2026],
    ],
}

scrapps_and_save(symbols)
```
